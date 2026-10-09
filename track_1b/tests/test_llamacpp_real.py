"""The llama.cpp backend against the real engine (skipped unless llama-cpp-python is installed and TINY_GGUF points to
a small GGUF, e.g. ggml-org/models tinyllamas/stories260K.gguf; CI runs it). Reference: the same sequences evaluated
with logits_all=True, log-softmax at every candidate position."""
import os

import pytest

llama_cpp = pytest.importorskip("llama_cpp")
TINY = os.environ.get("TINY_GGUF")
pytestmark = pytest.mark.skipif(not TINY, reason="TINY_GGUF not set")


def test_backend_equals_logits_all_reference():
    from statute_twins.harness.backends.llamacpp import LlamaCpp, log_softmax_at
    be = LlamaCpp(TINY, n_ctx=512, n_threads=2, label="tiny")
    be.template = "{{ bos_token }}{{ messages[0]['content'] }}\n"
    ref = llama_cpp.Llama(model_path=TINY, n_ctx=512, logits_all=True, verbose=False, n_threads=2)
    rows = [dict(user="Once upon a time there was a cat", answer_prefix=" It was", convict=" happy", acquit=" very sad"),
            dict(user="Once upon a time there was a dog", answer_prefix="", convict=" The", acquit=" One day")]
    for row in rows:
        s = be.score(row)
        prompt = be.render(row["user"]) + row["answer_prefix"]
        pre = be.tok(prompt)
        for side, got in (("convict", s.lp_convict), ("acquit", s.lp_acquit)):
            full = be.tok(prompt + row[side])
            ref.reset()
            ref.eval(full)
            want = sum(log_softmax_at(ref.scores[k - 1], full[k]) for k in range(len(pre), len(full)))
            assert abs(got - want) < 1e-3, (row, side, got, want)
        assert abs(s.lo_conv) > 1e-6          # the two candidates really differ
