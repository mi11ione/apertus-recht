"""Backends against fake engines with known log-probabilities (no model needed): the forced-choice arithmetic, the KV
rewind and prefix reuse of the llama.cpp backend, vLLM prompt_logprobs parsing, and served-model checks."""
import hashlib
import math

import pytest

from statute_twins.harness.backends.base import parse_decision
from statute_twins.harness.backends.llamacpp import LlamaCpp, log_softmax_at
from statute_twins.harness.backends.openai_compat import OpenAICompat, ServedModelMismatch, candidate_logprob

V = 64


def logits_after(history):
    """Deterministic pseudo-logits for the next token given the full token history."""
    h = hashlib.sha256(bytes(t % 256 for t in history[-12:]) + len(history).to_bytes(4, "big")).digest()
    return [((h[i % 32] * (i + 7)) % 97) / 9.0 for i in range(V)]


class FakeLlama:
    metadata = {"tokenizer.chat_template": "{{ bos_token }}<u>{{ messages[0]['content'] }}</u><a>",
                "tokenizer.ggml.bos_token_id": "1", "tokenizer.ggml.eos_token_id": "2"}

    def __init__(self):
        self.n_tokens = 0
        self.input_ids = []
        self.scores = [[0.0] * V for _ in range(4096)]
        self.evals = 0

    def tokenize(self, b, add_bos=False, special=True):
        return [3 + (c % (V - 3)) for c in b]          # one token per byte

    def detokenize(self, ids, special=True):
        return {1: b"<s>", 2: b"</s>"}.get(ids[0], b"?")

    def reset(self):
        self.n_tokens = 0

    def eval(self, toks):
        self.input_ids = self.input_ids[: self.n_tokens]
        for t in toks:
            self.input_ids.append(t)
            self.n_tokens += 1
            self.scores[self.n_tokens - 1] = logits_after(self.input_ids)
            self.evals += 1


def brute(llm, prompt_ids, cont):
    lp, hist = 0.0, list(prompt_ids)
    for t in cont:
        lp += log_softmax_at(logits_after(hist), t)
        hist.append(t)
    return lp


ROW = dict(user="Sachverhalt X", answer_prefix="Urteil:", convict=" schuldig", acquit=" nicht schuldig", lang="de", framing="ver")


def test_llamacpp_forced_choice_equals_brute_force_and_reuses_prefix():
    fake = FakeLlama()
    be = LlamaCpp("fake.gguf", llama=fake, label="fake")
    s = be.score(ROW)
    prompt = be.render(ROW["user"]) + ROW["answer_prefix"]
    pre = fake.tokenize(prompt.encode())
    for side, lp in (("convict", s.lp_convict), ("acquit", s.lp_acquit)):
        cont = fake.tokenize((prompt + ROW[side]).encode())[len(pre):]
        assert abs(lp - brute(fake, pre, cont)) < 1e-9
    first = fake.evals
    s2 = be.score(dict(ROW, user="Sachverhalt Y"))          # shares the template prefix
    assert s2.extra["reused"] > 0 and fake.evals - first < first
    s3 = be.score(ROW)                                       # back to the first prompt: identical scores
    assert abs(s3.lp_convict - s.lp_convict) < 1e-12 and abs(s3.lp_acquit - s.lp_acquit) < 1e-12


def test_log_softmax_normalises():
    xs = [0.3, -1.2, 4.0, 2.5]
    assert abs(sum(math.exp(log_softmax_at(xs, i)) for i in range(4)) - 1) < 1e-12


def _vllm_transport(model_served, lp_table):
    """Fake vLLM: echoes prompt_logprobs for the prefilled assistant content, token = one word piece per space."""
    def send(p):
        content = p["messages"][-1]["content"]
        pieces = []
        for w in content.replace("Urteil:", "Urteil: ").split(" "):
            if w:
                pieces.append(w if not pieces or w == "Urteil:" else " " + w)
        pl = [None] + [{str(i): dict(logprob=lp_table.get(t, -5.0), rank=2, decoded_token=t),
                        "999": dict(logprob=-0.01, rank=1, decoded_token="x")} for i, t in enumerate(pieces)]
        return dict(model=model_served, system_fingerprint="fake", prompt_logprobs=pl,
                    choices=[dict(message=dict(content=""), logprobs=None)])
    return send


def test_openai_exact_prefill_sums_candidate_tokens():
    table = {" schuldig": -0.5, " nicht": -3.0}
    be = OpenAICompat(base_url="x", model="m", mode="exact_prefill", transport=_vllm_transport("m", table))
    s = be.score(ROW)
    assert s.lp_convict == -0.5 and s.lp_acquit == -3.0 + -0.5 and s.method == "exact_prefill"


def test_served_model_mismatch_is_refused():
    be = OpenAICompat(base_url="x", model="swiss-ai/apertus-v1.5-70b", mode="exact_prefill",
                      transport=_vllm_transport("aisingapore/Qwen-SEA-LION-v4-32B-IT", {}))
    with pytest.raises(ServedModelMismatch):
        be.score(ROW)


def test_candidate_logprob_rejects_wrong_tokens():
    pl = [None, {"1": dict(logprob=-1.0, rank=1, decoded_token=" sch")}, {"2": dict(logprob=-0.2, rank=1, decoded_token="uld")}]
    with pytest.raises(ValueError):
        candidate_logprob(pl, " schuldig")
    assert candidate_logprob(pl + [{"3": dict(logprob=-0.1, rank=1, decoded_token="ig")}], " schuldig")[0] == pytest.approx(-1.3)


@pytest.mark.parametrize("lang, framing, text, want", [
    ("de", "conv", "Ja.", "convict"), ("de", "conv", "**Nein**, weil …", "acquit"), ("de", "ver", "Urteil: nicht schuldig", "acquit"),
    ("de", "ver", "schuldig", "convict"), ("fr", "conv", "Oui, car", "convict"), ("fr", "ver", "Jugement : non coupable", "acquit"),
    ("it", "conv", "No.", "acquit"), ("it", "conv", "Sì", "convict"), ("it", "ver", "Sentenza: colpevole", "convict"),
    ("de", "conv", "Das kommt darauf an.", "unparsed"),
])
def test_parse_decision(lang, framing, text, want):
    assert parse_decision(lang, framing, text) == want
