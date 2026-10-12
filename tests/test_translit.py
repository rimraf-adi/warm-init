from tone_donor.translit import to_devanagari

assert to_devanagari("ਕ", "pa") == "क"             # Gurmukhi KA -> Devanagari KA
assert to_devanagari("▁ਹ", "pa") == "▁ह"            # Gurmukhi HA, word-start marker kept
assert to_devanagari("ਘ", "pa") == "घ"
assert to_devanagari("ক", "bn") == "क"              # Bengali KA
assert to_devanagari("ক্ষ", "bn") == "क्ष"          # virama offset matches
assert to_devanagari("क", "hi") == "क"              # Devanagari donors untouched
assert to_devanagari("abc", "pa") == "abc"          # non-Indic characters untouched
print("translit ok")
