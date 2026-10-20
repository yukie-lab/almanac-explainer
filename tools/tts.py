"""Make one narration clip per line with Kokoro (kokoro-onnx) and record its length.

Usage: python tools/tts.py MODEL.onnx VOICES.bin [LINE_ID ...]
Writes tools/build/audio/<line id>.wav and tools/build/timing.json.
With line ids, only those clips are made again.
A line may carry "fix": pairs of phoneme strings to replace before synthesis
(for example, the letter "A" that the phonemizer reads as the article "a").
The model files are not in this repository (see README.md).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
AUDIO = BUILD / "audio"


def trim(samples, sr, thresh=0.004, pad=0.04):
    """Cut leading and trailing silence, keep a short pad."""
    idx = np.where(np.abs(samples) > thresh)[0]
    if len(idx) == 0:
        return samples
    a = max(0, idx[0] - int(pad * sr))
    b = min(len(samples), idx[-1] + int(pad * sr))
    return samples[a:b]


def synth(k, line, voice, speed):
    if line.get("fix"):
        ph = k.tokenizer.phonemize(line["say"], "en-us")
        for a, b in line["fix"]:
            if a not in ph:
                raise SystemExit(f"{line['id']}: phoneme string not found: {a}")
            ph = ph.replace(a, b)
        return k.create(ph, voice=voice, speed=speed, lang="en-us", is_phonemes=True)
    return k.create(line["say"], voice=voice, speed=speed, lang="en-us")


def main(model, voices, only):
    script = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
    AUDIO.mkdir(parents=True, exist_ok=True)
    k = Kokoro(model, voices)
    tpath = BUILD / "timing.json"
    old = json.loads(tpath.read_text(encoding="utf-8")) if (only and tpath.exists()) else {}
    olddur = {r["id"]: r["dur"] for rows in old.values() for r in rows}
    timing = {}
    for scene in script["scenes"]:
        rows = []
        for line in scene["lines"]:
            path = AUDIO / f"{line['id']}.wav"
            if only and line["id"] not in only and line["id"] in olddur:
                rows.append({"id": line["id"], "dur": olddur[line["id"]]})
                continue
            samples, sr = synth(k, line, script["voice"], script["speed"])
            samples = trim(np.asarray(samples, dtype=np.float32), sr)
            sf.write(path, samples, sr)
            dur = len(samples) / sr
            rows.append({"id": line["id"], "dur": round(dur, 3)})
            print(f"{line['id']:>5}  {dur:6.2f} s")
        timing[scene["id"]] = rows
    tpath.write_text(json.dumps(timing, indent=1), encoding="utf-8")
    total = sum(r["dur"] for rows in timing.values() for r in rows)
    print(f"total speech {total:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], set(sys.argv[3:]))
