import io
s = io.open('templates/index.html', encoding='utf-8', errors='replace').read()
lines = s.splitlines()
for i, l in enumerate(lines):
    if 'Auto-Flow' in l or 'autoflow' in l.lower() or 'autoFlow' in l:
        print('=== linha', i+1, '===')
        print('\n'.join(lines[i:i+12]))
        print()
