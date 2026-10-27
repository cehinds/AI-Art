"""Rebuild the request/result ledger from per-generation atomic records."""
import json, os
from pathlib import Path
OUT=Path(__file__).resolve().parent
rows=[]
for p in sorted((OUT/'repair-mappings').glob('*.json')):
    text=p.read_text()
    if text.endswith('\\n'):
        text=text[:-2]
    rows.append(json.loads(text))
target=OUT/'repair-mappings.json';tmp=target.with_suffix('.json.tmp');tmp.write_text(json.dumps(rows,indent=2)+'\n');os.replace(tmp,target)
