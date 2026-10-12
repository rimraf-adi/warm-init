from tone_donor.text import normalize, tone_cer
assert normalize("<static> field {field} chhungah [inhaling] <pause> a </static>") == "field field chhungah a"
assert normalize("ओह् जेह्ड़ा") == "ओह् जेह्ड़ा"
ref = "ओह् जाँदा"
assert tone_cer([(ref, ref)], "dogri")["tone_cer"] == 0
r = tone_cer([(ref, "ओ जाँदा")], "dogri")          # dropped ह्
assert r["tone_cer"] == 1.0 and r["cer"] > 0, r
r = tone_cer([(ref, "ओह् जाँदो")], "dogri")        # error away from tone chars
assert r["tone_cer"] == 0 and r["cer"] > 0, r
print("ok")
from tone_donor.text import tone_positions
r = "उं'दे ओह्"
assert len(tone_positions(r, "dogri", "apos")) == 1
assert len(tone_positions(r, "dogri", "ha")) == 2     # ह and virama
assert len(tone_positions(r, "dogri", "all")) == 3
print("ok2")
