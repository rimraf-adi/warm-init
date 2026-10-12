"""Approximate Indic script -> Devanagari mapping by Unicode block offset.

The Indic blocks follow the same ISCII-derived layout, so most letters, vowel signs and the virama sit at the
same offset from the block start. This is only used to decide which Dogri (Devanagari) tokenizer pieces
correspond to a donor language's pieces; it is not a faithful transliteration (script-specific signs such as
Gurmukhi tippi/addak/udaat have no exact counterpart and are left unmapped). The fraction of matched tokens is
logged with every run that uses it.
"""
DEVA = 0x0900
BLOCK_START = {
    "bn": 0x0980, "as": 0x0980,      # Bengali-Assamese
    "pa": 0x0A00,                    # Gurmukhi
    "gu": 0x0A80,
    "or": 0x0B00,
    "ta": 0x0B80,
    "te": 0x0C00,
    "kn": 0x0C80,
    "ml": 0x0D00,
}
DEVANAGARI_LANGS = {"hi", "mr", "ne", "doi", "brx", "mai", "kok", "sa"}


def to_devanagari(piece, lang):
    if lang in DEVANAGARI_LANGS or lang not in BLOCK_START:
        return piece
    start = BLOCK_START[lang]
    out = []
    for ch in piece:
        o = ord(ch)
        out.append(chr(o - start + DEVA) if start <= o < start + 0x80 else ch)
    return "".join(out)
