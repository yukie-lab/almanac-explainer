#!/bin/sh
# Render the named scenes of tools/video.py at 1920x1080 and 30 fps, three at a time.
# Usage: sh tools/render.sh S1 S2 ... S9   (needs manim on the PATH; run tools/tts.py first)
cd "$(dirname "$0")/.." || exit 1
mkdir -p tools/build/logs
for s in "$@"; do echo "$s"; done | xargs -P 3 -I{} sh -c 'manim render -r 1920,1080 --fps 30 --media_dir tools/build/media -o {}.mp4 tools/video.py {} > tools/build/logs/{}.log 2>&1; echo "{} exit $?"'
