import io, os
for fn in ['app.py', 'core_server.py', 'pluto_adapter.py', 'soultv_adapter.py', 'xtream_adapter.py']:
    s = io.open(fn, encoding='utf-8', errors='replace').read()
    lines = s.splitlines()
    for i, l in enumerate(lines):
        if 'roduz' in l or 'roduzindo' in l.lower():
            print(f'### {fn} linha {i+1} ###')
            print('\n'.join(lines[i:i+14]))
            print()
