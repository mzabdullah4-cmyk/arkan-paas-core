import json, os, time
import redis, requests

REDIS_URL=os.getenv("REDIS_URL","redis://redis-broker:6379/0")
CONTROL=os.getenv("CONTROL_PLANE_URL","http://control-plane:8000")
TOKEN=os.getenv("ARKAN_INTERNAL_TOKEN")
ENGINES={"sqlglot":(os.getenv("SQLGLOT_URL","http://sqlglot-worker:8000"),"sql"),"proleap":(os.getenv("PROLEAP_URL","http://cobol-worker:8000"),"source")}

def headers(): return {"Authorization":f"Bearer {TOKEN}"} if TOKEN else {}
def post(path, body=None):
    r=requests.post(CONTROL+path,json=body or {},headers=headers(),timeout=30); r.raise_for_status(); return r.json()
def process(item, client):
    ident=item["job_id"]
    try:
        post(f"/internal/jobs/{ident}/running")
        payload=requests.get(f"{CONTROL}/internal/jobs/{ident}/payload",headers=headers(),timeout=30); payload.raise_for_status(); data=payload.json()
        base,field=ENGINES.get(data["engine"],(None,None))
        if not base: raise ValueError(f"Unsupported engine: {data['engine']}")
        response=requests.post(base+"/analyze",json={field:data["content"]},timeout=300); response.raise_for_status(); analysis=response.json()
        if analysis.get("status")=="error": raise ValueError(analysis.get("error","engine failed"))
        result={"schema_version":"1.0","job_id":ident,"engine":data["engine"],"source":{"artifact_id":data["artifact_id"],"name":data["name"],"language":data["language"],"sha256":data.get("sha256")},"entities":analysis.get("ast",{}).get("tables",[]),"dependencies":analysis.get("dependencies",[]),"findings":analysis.get("findings",[]),"raw":analysis}
        post(f"/internal/jobs/{ident}/complete",{"result":result})
    except Exception as exc:
        attempt=int(item.get("attempt",0))+1; max_attempts=int(data.get("max_attempts",3)) if "data" in locals() else 3
        if attempt < max_attempts:
            time.sleep(min(2**attempt,30)); client.lpush("arkan:jobs",json.dumps({**item,"attempt":attempt})); return
        client.lpush("arkan:jobs:dead",json.dumps({**item,"attempt":attempt,"error":str(exc)})); post(f"/internal/jobs/{ident}/complete",{"error":f"permanent failure after {attempt} attempts: {exc}"})
def main():
    client=redis.Redis.from_url(REDIS_URL,decode_responses=True)
    while True:
        _,raw=client.brpop("arkan:jobs",timeout=5) or (None,None)
        if raw: process(json.loads(raw),client)
if __name__=="__main__": main()
