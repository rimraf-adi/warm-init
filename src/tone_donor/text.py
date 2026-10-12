"""Transcript normalization and tone-context CER."""
import re
import unicodedata

# VAANI annotation tags: <pause>, <static>...</static>, [inhaling], {word} -> word
_TAG = re.compile(r"</?[a-z_]+>|\[[^\]]*\]")
_BRACE = re.compile(r"\{([^}]*)\}")

# Characters whose presence in the reference marks a tone-bearing context.
# Dogri (checked on IndicVoices): ha+virama and the ASCII apostrophe.
# Punjabi: voiced aspirates and ha (Unicode ch.12: they combine consonant and tone).
TONE_CHARS = {
    "dogri": set("ह'ʼ्"),          # virama counted only next to ha, see _tone_positions
    "punjabi": set("ਘਝਢਧਭਹ"),
}
ASPIRATES_DEVANAGARI = set("घझढधभ")
PLAIN_DEVANAGARI = set("गजडदब")


def normalize(text, keep_tags=False, drop_apos=False):
    t = unicodedata.normalize("NFC", text)
    if drop_apos:
        t = t.replace("'", "").replace("ʼ", "").replace("’", "")
    if not keep_tags:
        t = _BRACE.sub(r"\1", t)
        t = _TAG.sub(" ", t)
    t = t.replace("’", "'")
    # drop punctuation/symbols only; keep letters, combining marks, digits, and the
    # apostrophe-like tone marks (Dogri uses them). \w would delete Indic vowel signs.
    t = "".join(c if (c in "'ʼ" or unicodedata.category(c)[0] not in "PS") else " " for c in t)
    return re.sub(r"\s+", " ", t).strip()


def _align(ref, hyp):
    """Levenshtein alignment; returns per-ref-char error flags (sub or del)."""
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                          d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]))
    err = [0] * n
    i, j = n, m
    while i > 0:
        if j > 0 and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1]):
            err[i - 1] = int(ref[i - 1] != hyp[j - 1]); i -= 1; j -= 1
        elif d[i][j] == d[i - 1][j] + 1:
            err[i - 1] = 1; i -= 1
        else:
            j -= 1
    return err, d[n][m]


def tone_positions(ref, lang, part="all"):
    """Indices of tone-bearing ref characters. For Dogri, part is "all", "ha"
    (ह and its virama) or "apos" (apostrophe marks; not in the IndicConformer vocab)."""
    pos = set()
    for i, ch in enumerate(ref):
        if lang == "dogri":
            if ch in "'ʼ" and part in ("all", "apos"):
                pos.add(i)
            if ch == "ह" and part in ("all", "ha"):
                pos.add(i)
                if i + 1 < len(ref) and ref[i + 1] == "्":
                    pos.add(i + 1)
        elif ch in TONE_CHARS.get(lang, ()):
            pos.add(i)
    return pos


def cer_stats(ref, hyp, positions=None):
    """Returns (total_edits, ref_len, errors_in_positions, n_positions)."""
    err, edits = _align(ref, hyp)
    if positions is None:
        positions = set()
    return edits, len(ref), sum(err[i] for i in positions), len(positions)


def tone_cer(pairs, lang, part="all"):
    """Corpus tone-context CER and overall CER over (ref, hyp) pairs."""
    E = N = TE = TN = 0
    for ref, hyp in pairs:
        e, n, te, tn = cer_stats(ref, hyp, tone_positions(ref, lang, part))
        E += e; N += n; TE += te; TN += tn
    return {"cer": E / max(N, 1), "tone_cer": TE / max(TN, 1), "tone_chars": TN, "chars": N}


def charset_cer(pairs, chars):
    """CER restricted to reference positions whose character is in `chars`."""
    errs = n = 0
    for ref, hyp in pairs:
        err, _ = _align(ref, hyp)
        for i, ch in enumerate(ref):
            if ch in chars:
                n += 1
                errs += err[i]
    return errs / max(n, 1), n
