#!/bin/zsh
# A22: verdict-only preference mirror (DE/FR/IT, R0) and the R5a ablations (German, Ja/Nein, the 80-group sample of
# A13/A15, --sample 240). 70B via the gateway under the name swiss-ai/apertus-v1.5-8b, exact forced choice, exactly as
# the A13 runs. Prompts: runs_a22/eval (python scripts/controls_a22.py build).
cd ~/Desktop/hackapertus/build/apertus-recht/track_1b
source .venv/bin/activate
export STATUTE_TWINS_GATEWAY=~/Desktop/hackapertus/gateway/gw.py
ev() { statute-twins eval --backend gateway --model swiss-ai/apertus-v1.5-8b --mode exact_prefill --dataset runs_a22 --out runs_a22 \
  --workers 6 --cap 1.0 "$@" || echo "FAILED $*"; }
for L in de fr it; do
  ev --run-id publicai-70b-prefv-$L --tag 1b-a22-prefv --parts prefv_core_$L --rungs R0 --framings prefv \
     --label "Apertus v1.5 70B via Public AI (name swiss-ai/apertus-v1.5-8b), chosen vs verdict-only mirror, exact (A22)"
done
ev --run-id publicai-70b-r5a-ablation-de --tag 1b-a22-r5abl --parts ctrl2_core_de --rungs R5a,R5ab,R5ac,R5ag,R5ad \
   --framings conv --sample 240 \
   --label "Apertus v1.5 70B via Public AI (name swiss-ai/apertus-v1.5-8b), exact forced choice, A22 R5a ablations"
echo ALLDONE
