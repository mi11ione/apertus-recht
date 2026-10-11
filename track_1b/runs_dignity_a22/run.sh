#!/bin/zsh
# A22: re-score only the dignity prompts whose text changed (the criticism variants); every unchanged prompt keeps its
# row (same request_sha256, skipped by the harness). Same model, method, gateway and scoring as the A18 runs.
cd ~/Desktop/hackapertus/build/apertus-recht/track_1b
source .venv/bin/activate
export STATUTE_TWINS_GATEWAY=~/Desktop/hackapertus/gateway/gw.py
for L in de fr it; do
  for k in 1 2; do   # a second pass re-scores only errored rows
    statute-twins eval --backend gateway --model swiss-ai/apertus-v1.5-8b --mode exact_prefill --dataset dataset/dignity \
      --out runs_dignity_a22 --workers 4 --cap 1.0 --run-id publicai-70b-dignity-$L --tag 1b-a22-dignity-$L \
      --parts dignity_$L --rungs R0,R3,R5 --framings conv,ver \
      --label "Apertus v1.5 70B via Public AI (name swiss-ai/apertus-v1.5-8b), exact forced choice, DIGNITY family (A18; criticism variants re-scored in A22)" \
      || echo "pass $k: some rows to retry ($L)"
  done
done
echo ALLDONE
