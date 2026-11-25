import re
s = open('app.py', encoding='utf-8').read()
m = re.search(r'@app\.route\("/api/dashboard".*?(?=\n@app\.route)', s, re.S)
print(m.group(0) if m else 'NAO ACHOU')
