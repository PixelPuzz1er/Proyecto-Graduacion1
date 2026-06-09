import re
from pathlib import Path
path = Path(r'C:\Users\Angel\AppData\Local\Programs\Microsoft VS Code\8761a5560c\resources\app\extensions\copilot\package.json')
text = path.read_text(encoding='utf-8', errors='ignore')
idx = text.index('"vendor":"customendpoint"')
start = max(0, idx - 1000)
end = min(len(text), idx + 3500)
print(text[start:end])
