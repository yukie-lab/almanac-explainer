"""Join the rendered scenes, lay the voice clips at their beat marks, and write the subtitles.

Usage: python tools/assemble.py MEDIA_DIR
MEDIA_DIR holds the scene videos S1.mp4 ... S9.mp4 rendered by tools/video.py.
Writes assets/video/almanac-explainer.mp4, poster.jpg, subs.en.vtt, subs.ja.vtt, chapters.json.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
OUT = HERE.parent / "assets" / "video"
LEAD = 0.12      # the voice starts this long after its beat mark
SR = 24000
EN_MAX = 84      # characters per cue (two lines of about 42)
JA_MAX = 40      # characters per cue (two lines of about 20)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(path)], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def split_text(text, limit, seps):
    """Split text at the separator nearest its middle until every piece fits the limit."""
    if len(text) <= limit:
        return [text]
    mid = len(text) / 2
    best = None
    for sep in seps:
        for m in re.finditer(re.escape(sep), text):
            cut = m.end()
            if 0 < cut < len(text) and (best is None or abs(cut - mid) < abs(best - mid)):
                best = cut
        if best is not None and abs(best - mid) < len(text) * 0.3:
            break
    if best is None:
        best = text.rfind(" ", 0, int(mid)) + 1 or int(mid)
    a, b = text[:best].strip(), text[best:].strip()
    return split_text(a, limit, seps) + split_text(b, limit, seps)


def stamp(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def cues(start, end, pieces):
    total = sum(len(p) for p in pieces)
    t = start
    out = []
    for p in pieces:
        d = (end - start) * len(p) / total
        out.append((t, t + d, p))
        t += d
    return out


def main(media):
    media = Path(media)
    script = json.loads((HERE / "narration.json").read_text(encoding="utf-8"))
    timing = json.loads((BUILD / "timing.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    scenes = [s["id"] for s in script["scenes"]]
    files = [media / f"{sid.upper()}.mp4" for sid in scenes]
    durs = [duration(f) for f in files]
    total = sum(durs)

    lst = BUILD / "concat.txt"
    lst.write_text("".join(f"file '{f.resolve()}'\n" for f in files), encoding="utf-8")
    joined = BUILD / "joined.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(joined)], check=True)

    voice = np.zeros(int((total + 1.0) * SR), dtype=np.float32)
    en_cues, ja_cues = [], []
    offset = 0.0
    for sid, scene, d in zip(scenes, script["scenes"], durs):
        marks = json.loads((BUILD / "marks" / f"{sid}.json").read_text(encoding="utf-8"))["marks"]
        for line, row, mark in zip(scene["lines"], timing[sid], marks):
            clip, sr = sf.read(BUILD / "audio" / f"{line['id']}.wav", dtype="float32")
            assert sr == SR
            start = offset + mark + LEAD
            i = int(round(start * SR))
            voice[i:i + len(clip)] += clip
            end = start + row["dur"]
            en_cues += cues(start, end, split_text(line["en"], EN_MAX, [": ", "; ", ", ", " and ", " so "]))
            ja_cues += cues(start, end, split_text(line["ja"], JA_MAX, ["。", "、"]))
        offset += d
    voice = np.clip(voice * 0.95, -1, 1)
    wav = BUILD / "narration.wav"
    sf.write(wav, voice[: int(total * SR)], SR)

    mp4 = OUT / "almanac-explainer.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(wav),
                    "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-tune", "animation", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                    "-metadata", "title=Where will Proxima b be when a probe arrives?",
                    "-metadata", "comment=Synthetic voice (Kokoro-82M). Made with the help of AI. CC BY 4.0.",
                    str(mp4)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "2.4", "-i", str(mp4), "-frames:v", "1",
                    "-vf", "scale=1280:-2", "-q:v", "3", str(OUT / "poster.jpg")], check=True)

    for name, cl in (("subs.en.vtt", en_cues), ("subs.ja.vtt", ja_cues)):
        body = ["WEBVTT", ""]
        for n, (a, b, text) in enumerate(cl, 1):
            body += [str(n), f"{stamp(a)} --> {stamp(b)}", esc(text), ""]
        (OUT / name).write_text("\n".join(body), encoding="utf-8")

    starts = np.concatenate([[0.0], np.cumsum(durs)[:-1]])
    chapters = [{"id": s["id"], "title": s["title"], "title_ja": s["title_ja"], "start": round(float(t), 2)}
                for s, t in zip(script["scenes"], starts)]
    (OUT / "chapters.json").write_text(json.dumps({"duration": round(total, 2), "chapters": chapters},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"video {total:.2f} s, {mp4.stat().st_size / 1e6:.1f} MB; cues en {len(en_cues)}, ja {len(ja_cues)}")


if __name__ == "__main__":
    main(sys.argv[1])
