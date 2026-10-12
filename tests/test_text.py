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
