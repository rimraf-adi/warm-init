"""Stream a VAANI language subset from Hugging Face without downloading it.

The token is read from the HF_TOKEN environment variable; it is never stored.

    uv run python -m tone_donor.vaani_stream Mizo --n 5
    uv run python -m tone_donor.vaani_stream Mizo --hours 1 --out data/manifest_mizo.jsonl
"""
import argparse
import io
import json
import os
import sys

import soundfile as sf
from datasets import Audio, load_dataset

REPO = "ARTPARK-IISc/VAANI"


def _load_dotenv(path=".env"):
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            k, _, v = line.strip().partition("=")
            if k and v and not k.startswith("#"):
                os.environ.setdefault(k, v)


def stream_language(language, split="train"):
    _load_dotenv()
    token = os.environ.get("HF_TOKEN")
    if not token:
        sys.exit("Set HF_TOKEN in the environment first.")
    ds = load_dataset(REPO, language, split=split, streaming=True, token=token)
    # keep raw bytes; decoded with soundfile (avoids the torchcodec dependency)
    return ds.cast_column("audio", Audio(decode=False))


def duration_s(audio):
    if audio and audio.get("bytes"):
        info = sf.info(io.BytesIO(audio["bytes"]))
        return info.frames / info.samplerate
    return 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("language")
    ap.add_argument("--split", default="train")
    ap.add_argument("--n", type=int, default=0, help="stop after n examples")
    ap.add_argument("--hours", type=float, default=0, help="stop after this many hours of audio")
    ap.add_argument("--all-rows", action="store_true", help="include untranscribed rows")
    ap.add_argument("--out", help="JSONL manifest of metadata and transcripts, no audio")
    args = ap.parse_args()

    ds = stream_language(args.language, args.split)
    if not args.all_rows:
        # most VAANI rows have no transcript; keep only transcribed ones
        ds = ds.filter(lambda ex: ex["isTranscriptionAvailable"] == "Yes" and bool(ex["transcript"]))
    print("features:", ds.features, file=sys.stderr)

    seconds, count = 0.0, 0
    out = open(args.out, "w", encoding="utf-8") if args.out else None
    for ex in ds:
        dur = duration_s(ex.get("audio"))
        seconds += dur
        meta = {k: v for k, v in ex.items() if k != "audio"}
        meta["duration_s"] = round(dur, 3)
        if out:
            out.write(json.dumps(meta, ensure_ascii=False, default=str) + "\n")
        else:
            print(meta)
        count += 1
        if args.n and count >= args.n:
            break
        if args.hours and seconds >= args.hours * 3600:
            break
    if out:
        out.close()
    print(f"{count} examples, {seconds / 3600:.3f} h audio", file=sys.stderr)


if __name__ == "__main__":
    main()
