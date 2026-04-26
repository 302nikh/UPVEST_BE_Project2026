import zlib, requests, os

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

source_path = os.path.join(os.getcwd(), 'system_architecture.puml')
if not os.path.exists(source_path):
    source_path = os.path.join(os.getcwd(), 'frontend', 'system_architecture.puml')
source = open(source_path).read()
encoded = encode_plantuml(source)
url = f"http://www.plantuml.com/plantuml/png/{encoded}"
print('fetching', url)
resp = requests.get(url)
if resp.status_code == 200:
    out_path = os.path.splitext(source_path)[0] + '.png'
    with open(out_path, 'wb') as f:
        f.write(resp.content)
    print('Saved', out_path)
else:
    print('render failed', resp.status_code)
