import os

print('cwd', os.getcwd())

try:
    from plantuml import PlantUML
    print('imported PlantUML class')
    p = PlantUML(url='http://www.plantuml.com/plantuml/img/')
    # try render online (requires network)
except Exception as e:
    print('plantuml import error', e)

# fallback: just show file exists
for fname in ['architecture.puml','dfd-plantuml.puml','system_architecture.puml']:
    print(fname, 'exists?', os.path.exists(fname))

# try local PlantUML module if available
try:
    from plantuml import PlantUML
    plantuml_available = True
    p = PlantUML(url='http://www.plantuml.com/plantuml/img/')
except Exception as e:
    plantuml_available = False
    print('plantuml module not usable:', e)

# if local module worked, render the files
if plantuml_available:
    for fname in ['architecture.puml','dfd-plantuml.puml','system_architecture.puml']:
        if os.path.exists(fname):
            print('local render', fname)
            success = p.processes_file(fname)
            print('->', fname, 'ok?', success)
else:
    # fall back to online URL method
    import requests
    import zlib
    import base64
    PLANTUML_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    def encode_plantuml(text: str) -> str:
        data = text.encode('utf-8')
        compressed = zlib.compress(data)[2:-4]
        result = ""
        current = 0
        bits = 0
        for byte in compressed:
            current = (current << 8) | byte
            bits += 8
            while bits >= 6:
                bits -= 6
                index = (current >> bits) & 0x3F
                result += PLANTUML_CHARS[index]
        if bits > 0:
            current <<= (6 - bits)
            index = current & 0x3F
            result += PLANTUML_CHARS[index]
        return result
    def render_online(source, outpath):
        encoded = encode_plantuml(source)
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        resp = requests.get(url)
        if resp.status_code == 200 and resp.headers.get('Content-Type','').startswith('image'):
            with open(outpath, 'wb') as f:
                f.write(resp.content)
            print('saved', outpath)
        else:
            print('online render failed', resp.status_code, resp.headers.get('Content-Type'))
    for fname in ['architecture.puml','dfd-plantuml.puml']:
        if os.path.exists(fname):
            txt = open(fname).read()
            pngname = fname.replace('.puml','.png')
            render_online(txt, pngname)
