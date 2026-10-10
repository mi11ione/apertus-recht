# The submission lives in track_1b/; these targets delegate so `make run` works from the repository root as well.
.PHONY: run run-gguf test local
run run-gguf test local:
	$(MAKE) -C track_1b $@
