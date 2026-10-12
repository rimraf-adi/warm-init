"""Phase 0: sample each pool language from VAANI (streaming) and record script,
transcript tags and sampled hours. Writes results/vaani_survey.json."""
import json
import re
import sys
import unicodedata
from collections import Counter

from tone_donor.vaani_stream import stream_language

POOL = ["Mizo", "Wancho", "Tulu", "Chhattisgarhi", "Kokborok", "Sumi", "Garo", "Chakma",
        "Garhwali", "Kumaoni", "Nagamese", "Bhojpuri", "Marwari", "Magahi", "Bajjika",
        "Maithili", "Nepali", "Odia", "Konkani", "Punjabi", "Dogri", "Bodo", "Manipuri",
        "Santali", "Hindi", "Bengali", "Marathi", "Assamese", "Kannada"]
TAG = re.compile(r"<[^>]+>|\[[^\]]+\]|\{[^}]*\}")


def script_of(ch):
    try:
        return unicodedata.name(ch).split()[0]
    except ValueError:
        return None


def survey(lang, n):
    ds = stream_language(lang).filter(
        lambda ex: ex["isTranscriptionAvailable"] == "Yes" and bool(ex["transcript"]))
    scripts, tags, secs, k = Counter(), Counter(), 0.0, 0
    for ex in ds:
        t = ex["transcript"]
        tags.update(TAG.findall(t))
        for ch in TAG.sub("", t):
            if ch.isalpha():
                scripts[script_of(ch)] += 1
        secs += ex["duration"]
        k += 1
        if k >= n:
            break
    return {"rows": k, "hours": round(secs / 3600, 3),
            "scripts": scripts.most_common(4), "top_tags": tags.most_common(8)}


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    out = {}
    for lang in POOL:
        try:
            out[lang] = survey(lang, n)
            print(lang, out[lang]["rows"], out[lang]["scripts"][:2], flush=True)
        except Exception as e:
            out[lang] = {"error": f"{type(e).__name__}: {str(e)[:150]}"}
            print(lang, "ERROR", out[lang]["error"], flush=True)
        json.dump(out, open("results/vaani_survey.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
