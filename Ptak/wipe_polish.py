import os

replacements = {
  'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
  'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
}

files = ['start_game.sh', 'start_server.sh', 'server.py']
for fname in files:
    if os.path.exists(fname):
        with open(fname, 'r', encoding='utf-8') as f:
            content = f.read()
        for k, v in replacements.items():
            content = content.replace(k, v)
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content)
print("Done wiping Polish characters.")
