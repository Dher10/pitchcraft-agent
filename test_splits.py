import urllib.request, json
url = "https://statsapi.mlb.com/api/v1/teams/110/stats?stats=statSplits&sitCodes=vl,vr&group=hitting&season=2026"
req = urllib.request.Request(url, headers={"User-Agent": "PitchCraft/1.0"})
with urllib.request.urlopen(req, timeout=8) as r:
    data = json.loads(r.read())
for s in data.get("stats", []):
    for sp in s.get("splits", [{}]):
        code = sp.get("split", {}).get("code")
        st = sp.get("stat", {})
        print(f"vs {code}: OPS={st.get('ops')}, AVG={st.get('avg')}, K={st.get('strikeOuts')}, BB={st.get('baseOnBalls')}, PA={st.get('plateAppearances')}")