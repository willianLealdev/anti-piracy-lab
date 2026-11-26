import io
s = io.open('templates/index.html', encoding='utf-8', errors='replace').read()
lines = s.splitlines()
for i, l in enumerate(lines):
    if 'roduz' in l or 'roduzindo' in l.lower():
        print('=== linha', i+1, '===')
        print('\n'.join(lines[i:i+22]))
        print()
