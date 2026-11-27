"""Reassemble base64 image chunks returned by the browser ('#<TAG><n>#...#END#'). usage: chunks.py TAG N outdir"""
import json, glob, re, base64, sys, os
tag, n, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
parts = {}
for f in glob.glob('/tmp/claude-tool-results/*/*javascript_tool*.txt'):
    try: t = json.load(open(f))[0]['text']
    except Exception: continue
    if t.startswith('"'):
        try: t, _ = json.JSONDecoder().raw_decode(t)
        except Exception: continue
    m = re.match(r'#' + tag + r'(\d+)#', t)
    if m and '#END#' in t: parts[int(m.group(1))] = t[m.end():t.index('#END#')]
missing = [i for i in range(n) if i not in parts]
if missing: sys.exit(f"missing chunks {missing}")
d = json.loads(''.join(parts[i] for i in range(n)))
os.makedirs(out, exist_ok=True)
for k, v in d.items(): open(os.path.join(out, f"{k}.jpg"), 'wb').write(base64.b64decode(v)); print(k)
