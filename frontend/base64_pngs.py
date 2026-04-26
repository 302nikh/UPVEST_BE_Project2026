import base64, os
for fname in ['architecture.png','dfd-plantuml.png']:
    path = os.path.join(os.getcwd(), fname)
    print(f"---{fname} exists? {os.path.exists(path)}---")
    with open(path,'rb') as f:
        data = f.read()
    print(base64.b64encode(data)[:100])
