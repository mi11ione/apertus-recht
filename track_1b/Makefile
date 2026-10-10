# Apertus-Recht (Hack Apertus track 1B). `make run` is the judges' entry point: Docker, CPU, clean checkout.
#   step 1  re-derive every item and gold label from the statute YAML and compare hashes   (no model, seconds)
#   step 2  re-score every stored model response and compare with results/results.json     (no model, seconds)
#   step 3  live slice on a model, checked against reference bands                         (only if configured)
# Live slice: set LLM_NAME, LLM_BASE_URL, LLM_API_KEY (any OpenAI-compatible endpoint) for LIVE=api, or LIVE=gguf to
# download the public Q4_K_M GGUF of Apertus v1.5 8B (5.1 GB, sha256-checked) and score it on CPU with llama.cpp.
IMAGE ?= apertus-recht:1.0
LIVE ?= $(if $(LLM_BASE_URL),api,)
LIVE_ITEMS ?= 30

.PHONY: run run-gguf test build-image local

run:
	docker build -q --target base -t $(IMAGE) .
	docker run --rm -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e LLM_MODE $(IMAGE) \
	  selfcheck $(if $(LIVE),--live $(LIVE) --live-items $(LIVE_ITEMS),)

run-gguf:
	docker build -q --target gguf -t $(IMAGE)-gguf .
	docker run --rm -v statute-twins-models:/models $(IMAGE)-gguf selfcheck --live gguf --live-items $(LIVE_ITEMS)

test:
	docker build -q --target base -t $(IMAGE) .
	docker run --rm --entrypoint sh $(IMAGE) -c "pip install -q pytest==8.3.3 jinja2==3.1.4 numpy==2.1.3 && python -m pytest -q tests"

# without Docker (Python >= 3.10): pip install -e . && make local
local:
	statute-twins selfcheck $(if $(LIVE),--live $(LIVE) --live-items $(LIVE_ITEMS),)
