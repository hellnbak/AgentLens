import json, os, pathlib, re
from fastapi import FastAPI
app=FastAPI(title="AgentLens MCP Inventory", version="0.1.0")
SEARCH=[pathlib.Path.home()/'.config', pathlib.Path.home()/'.cursor', pathlib.Path.cwd()]
RISKY=re.compile(r'(token|secret|password|key|env|shell|bash|curl|wget|filesystem)', re.I)

def scan():
    out=[]
    for base in SEARCH:
        if not base.exists(): continue
        for p in list(base.rglob('*mcp*.json'))[:200]:
            try:
                data=json.loads(p.read_text(errors='ignore'))
                text=json.dumps(data)
                risk=70 if RISKY.search(text) else 25
                out.append({'path':str(p),'risk_score':risk,'risky_keywords':sorted(set(RISKY.findall(text))), 'servers': data.get('mcpServers') or data.get('servers') or data})
            except Exception as e:
                out.append({'path':str(p),'error':str(e),'risk_score':10})
    return out
@app.get('/health')
def health(): return {'status':'ok'}
@app.get('/inventory')
def inventory(): return {'items': scan()}
