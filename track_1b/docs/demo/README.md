# Demo film

`apertus-recht-demo.mp4` (1920×1080, 30 fps, about 1:50, English narration with burned-in subtitles) is built by the
Remotion project in `/Users/mi11ion/Desktop/hackapertus/build/apertus-recht-film/` (outside this repository).
The film is one continuous sheet: every square is one scenario of the dataset, and its colour at each step is the
stored model response for that item (pink with a red edge = the model contradicts the law).

## Re-render

```sh
cd /Users/mi11ion/Desktop/hackapertus/build/apertus-recht-film
npm install          # once
make                 # extract -> voice -> render -> loudness pass -> copy here -> three motion excerpts
```

`make` runs, in order:

1. `pipeline/extract.py` reads every cell, number, quote and label from this repository: items and gold verdicts from
   `dataset/eval/*.jsonl`, per-item decisions from the response files in `dataset/responses/` (not from
   `results/results.json`), the R4 sentence and the R5 law text from the prompts, the step titles and their status from
   `statute-twins selfcheck` (what `make run` runs). It checks each narration sentence (`pipeline/script.py`) against
   those values and rewrites `narration.md` here. If a sentence no longer matches the data, it stops and names the
   sentence; edit `pipeline/script.py` and run `make` again. It also stops if the self-check fails, because the film
   shows the steps ticking; `make DRAFT=1` renders the status as it is instead.
2. `pipeline/tts.py` voices one audio file per sentence and re-voices only sentences whose text changed (cached by text
   hash in `pipeline/cache/`). All motion is timed from the measured audio and its character timestamps.
3. `npx remotion render` draws the frames; ffmpeg normalises loudness to -16 LUFS and writes the file here;
   `pipeline/excerpts.py` cuts three short clips to `out/excerpts/` (pull-back, R3 sweep and regroup, R5 ribbon and
   sweep).

Use another checkout with `make REPO=/path/to/track_1b`. `node pipeline/stills.mjs out/stills <frame>:<name> ...`
renders single frames, `pipeline/sheets.sh <mp4> <dir> name:start:dur:fps ...` makes contact sheets of a move, and
`python3 pipeline/stt_check.py <mp4>` transcribes the film to check how names and numbers are read.

## Tools

Remotion 4.0.534 (React); ElevenLabs `eleven_multilingual_v2`, voice "Artaius - Calm British Narrator" (voice
library), speed 1.0, stability 0.85, style 0 (API key read from `~/.config/elevenlabs/key` by the scripts, never
stored); ffmpeg; fonts Source Sans 3 and IBM Plex Mono from `docs/fonts/` (OFL).

`narration.md` is the spoken text, sentence by sentence, with the source of every number and of what is on screen.
