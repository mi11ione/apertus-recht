# Demo film

`apertus-recht-demo.mp4` (1920×1080, 30 fps, about 1:53, English narration with burned-in subtitles) is built by the
Remotion project in `/Users/mi11ion/Desktop/hackapertus/build/apertus-recht-film/` (outside this repository).

## Re-render

```sh
cd /Users/mi11ion/Desktop/hackapertus/build/apertus-recht-film
npm install          # once
make                 # extract -> voice -> render -> loudness pass -> copy here
```

`make` runs, in order:

1. `pipeline/extract.py` reads every number, quote and label from this repository (`results/results.json`,
   `dataset/eval/*.jsonl`, `dataset/responses/publicai-70b-fc-lay.jsonl`, `Makefile`), checks each narration sentence
   (`pipeline/script.py`) against those values, and rewrites `narration.md` here. If a sentence no longer matches the
   data, for example because a count changed, it stops and names the sentence; edit `pipeline/script.py` and run
   `make` again.
2. `pipeline/tts.py` voices one audio file per sentence and re-voices only the sentences whose text changed (cached by
   text hash in `pipeline/cache/`). Scene timing comes from the measured audio and the character timestamps.
3. `npx remotion render` draws the frames; ffmpeg normalises loudness to -16 LUFS and writes the file here.

Use another checkout with `make REPO=/path/to/track_1b`. `make stills` renders one still per scene to `out/stills/`;
`python3 pipeline/stt_check.py <mp4>` transcribes the film to check how names and numbers are read.

## Tools

Remotion 4.0.534 (React); ElevenLabs `eleven_multilingual_v2`, voice "Artaius - Calm British Narrator" (voice
library), speed 1.0, stability 0.85, style 0, 0.5-0.9 s between sentences and 1.2 s between scenes (API key read
from `~/.config/elevenlabs/key` by the scripts, never stored); ffmpeg; fonts Source Sans 3 and IBM Plex Mono from
`docs/fonts/` (OFL).

`narration.md` is the spoken text, sentence by sentence, with the source of every number.
