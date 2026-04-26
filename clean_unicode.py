# Clean unicode from file
import re

with open('simple_paper_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove all unicode characters
content = re.sub(r'[^\x00-\x7F]+', '', content)

# Replace common unicode patterns
content = content.replace('', '[OK]')
content = content.replace('', '[X]')
content = content.replace('', '[!]')
content = content.replace('', '[PAUSE]')
content = content.replace('', '[CLOCK]')
content = content.replace('', '[CHART]')
content = content.replace('', '[BULB]')
content = content.replace('', '[ROCKET]')
content = content.replace('', '[LOOP]')
content = content.replace('', '[STOP]')

with open('bot_clean.py', 'w', encoding='ascii', errors='ignore') as f:
    f.write(content)

print("File cleaned successfully!")
