import io
s = io.open('app.py', encoding='utf-8', errors='replace').read()
lines = s.splitlines()
print('\n'.join(lines[0:60]))
