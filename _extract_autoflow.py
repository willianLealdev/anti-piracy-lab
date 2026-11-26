import io
s = io.open('app.py', encoding='utf-8', errors='replace').read()
lines = s.splitlines()
# find autoflow section
start = None
for i, l in enumerate(lines):
    if 'AUTO-FLOW' in l.upper() or 'autoflow' in l.lower():
        start = i
        break
if start is not None:
    print('\n'.join(lines[start:start+220]))
