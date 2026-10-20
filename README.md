# Where will Proxima b be when a probe arrives?

A plain-language guide, with a short animated video, to the paper

> Maeda, Y. (2026). *How well can the position of Proxima Centauri b at a probe's arrival be known before launch?* (Version 0.4). Zenodo. https://doi.org/10.5281/zenodo.23501923

The page is in English, with a Japanese version behind a switch at the top. The video has English narration and subtitles in English and Japanese. The page uses only the paper's own results; if the page and the paper differ, the paper is correct.

日本語: 上の論文を一般の方向けに解説する、動画つきのページです。英語が先で、上のボタンで日本語に切り替えられます。動画の語りは英語で、字幕は英語と日本語があります。

## Files

| Path | What it is |
|---|---|
| `index.html` | The page (built from `tools/page.html`; do not edit it by hand) |
| `assets/css/site.css`, `assets/js/site.js` | Styles; language switch, subtitle choice, transcript buttons |
| `assets/video/` | The video (H.264/AAC MP4), poster, subtitles (`subs.en.vtt`, `subs.ja.vtt`), chapter times |
| `tools/` | Everything that makes the video and the page (not needed to serve the site) |

The site is static: no build step, no framework, no external requests.

## Publish with Vercel

1. Sign in at vercel.com with GitHub, and choose **Add New… → Project**.
2. Import `yukie-lab/almanac-explainer`. If Vercel cannot see the repository, give the Vercel GitHub app access to it when it asks.
3. Settings: **Framework Preset: Other**. Root Directory: `./`. Leave the Build Command and the Output Directory empty.
4. Choose **Deploy**. Each later push to `main` publishes again.

`.vercelignore` keeps `tools/` off the published site.

## Make the video and the page again

You need Python 3.11 or later, ffmpeg, and the font CMU Serif (Debian/Ubuntu: `fonts-cmu`).

```sh
python -m venv .venv && . .venv/bin/activate
pip install "manim==0.22.*" kokoro-onnx soundfile numpy

# The voice model (Kokoro-82M, Apache License 2.0). Keep these files outside the repository or let .gitignore skip them.
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

python tools/tts.py kokoro-v1.0.onnx voices-v1.0.bin           # one voice clip per line, and their lengths
sh tools/render.sh S1 S2 S3 S4 S5 S6 S7 S8 S9                   # the nine scenes, 1920x1080 at 30 fps
python tools/assemble.py tools/build/media/videos/video/1080p30  # video, poster, subtitles, chapter times
python tools/build_page.py                                       # index.html, with the figures and the transcript
```

The words of the video are in `tools/narration.json`: `say` is what the voice reads, `en` and `ja` are the subtitles and the transcript. The page text is in `tools/page.html`. The picture waits for each voice line, so the voice and the subtitles stay in step after any change.

## How this was made

Claude (Anthropic), an AI model, wrote the text, the figures, the video script, the animation code, and the page, at the request of the paper's author. The animation uses Manim Community Edition. The voice is synthetic: Kokoro-82M, run with kokoro-onnx.

## License

Everything in this repository is available under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
