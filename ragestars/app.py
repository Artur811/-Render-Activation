import os, re, hmac, hashlib, secrets, uuid, calendar
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify, Response
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8192
PLANS = {"minute": "1 минута", "week": "1 неделя", "month": "1 месяц", "forever": "Навсегда"}
DDL = """
CREATE TABLE IF NOT EXISTS ragestars_licenses (
 id UUID PRIMARY KEY, code_hash TEXT UNIQUE NOT NULL, code_hint TEXT NOT NULL,
 plan TEXT NOT NULL CHECK (plan IN ('minute','week','month','forever')),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(), installation_hash TEXT,
 activated_at TIMESTAMPTZ, expires_at TIMESTAMPTZ, revoked BOOLEAN NOT NULL DEFAULT false
)
"""

def db():
    url=os.environ.get("DATABASE_URL","")
    if not url: raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(url, row_factory=dict_row)

def init_db():
    with db() as c: c.execute(DDL)

def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def admin_ok():
    secret=os.environ.get("ADMIN_SECRET","")
    got=request.headers.get("X-Admin-Secret","")
    return bool(secret) and hmac.compare_digest(secret,got)

def expiry(start, plan):
    if plan=="forever": return None
    if plan=="minute": return start+timedelta(minutes=1)
    if plan=="week": return start+timedelta(days=7)
    if plan=="month":
        y=start.year+(start.month==12); m=start.month%12+1
        return start.replace(year=y,month=m,day=min(start.day,calendar.monthrange(y,m)[1]))
    raise ValueError("bad plan")

def token_for(license_id, install_hash):
    key=os.environ.get("TOKEN_SECRET","")
    if not key: raise RuntimeError("TOKEN_SECRET is not configured")
    return hmac.new(key.encode(),f"{license_id}:{install_hash}".encode(),hashlib.sha256).hexdigest()

@app.after_request
def headers(r):
    r.headers["Cache-Control"]="no-store"
    r.headers["X-Content-Type-Options"]="nosniff"
    r.headers["X-Frame-Options"]="DENY"
    return r

@app.get("/health")
def health():
    try:
        with db() as c: c.execute("SELECT 1")
        return jsonify(status="ok", service="RageStars")
    except Exception:
        app.logger.exception("health check failed")
        return jsonify(status="database_unavailable"),503

@app.get("/")
def home():
    return Response("""<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#10090d"><title>RageStars Admin</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b090c;color:#f6edf0;font:15px system-ui;min-height:100vh;padding:24px;background-image:radial-gradient(ellipse at 50% 0,#45121e 0,transparent 55%)}main{max-width:850px;margin:6vh auto;background:#151015;border:1px solid #4a202c;border-radius:18px;padding:24px;box-shadow:0 20px 80px #0009}h1{margin:0;color:#ff526c;letter-spacing:2px}p{color:#b9aab0}.row{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}input,select,button{border:1px solid #56303a;background:#0f0b0f;color:#fff;padding:12px;border-radius:9px;font:inherit}input{flex:1;min-width:220px}button{background:#a51e3c;border:0;font-weight:700;cursor:pointer}button:disabled{opacity:.5}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0b090c;border:1px solid #40232b;padding:14px;border-radius:10px;color:#ffc0ca;min-height:55px}.hint{font-size:12px;color:#96858c}</style><main><h1>RAGESTARS</h1><p>Панель управления одноразовыми лицензиями</p><div class="row"><input id="secret" type="password" placeholder="ADMIN_SECRET"><button id="save">Подключить</button></div><div id="panel" hidden><div class="row"><select id="plan"><option value="minute">1 минута</option><option value="week">1 неделя</option><option value="month">1 месяц</option><option value="forever">Навсегда (только администратор)</option></select><button id="create">Создать код</button><button id="refresh">Обновить список</button></div><pre id="result">Войдите, чтобы управлять лицензиями.</pre><div id="list"></div></div><p class="hint">Код одноразовый. Срок начинается при первой активации. Бессрочный код может создать только администратор.</p></main><script>
let secret="";const $=x=>document.getElementById(x);async function api(path,data={}){let r=await fetch(path,{method:"POST",headers:{"Content-Type":"application/json","X-Admin-Secret":secret},body:JSON.stringify(data)});let j=await r.json();if(!r.ok)throw Error(j.error||"Ошибка");return j}
$("save").onclick=async()=>{secret=$("secret").value;try{await api("/admin/list");$("panel").hidden=false;$("result").textContent="Администратор подключён." ;await load()}catch(e){$("result").textContent=e.message;secret=""}};
$("create").onclick=async()=>{try{let x=await api("/admin/codes",{plan:$("plan").value});$("result").textContent="НОВЫЙ КОД: "+x.code+"\nТариф: "+x.plan_label+"\nСрок начнётся после первой активации.";await load()}catch(e){$("result").textContent=e.message}};
$("refresh").onclick=load;
async function load(){try{let x=await api("/admin/list");$("list").innerHTML=x.licenses.map(v=>"<pre>"+v.code_hint+" · "+v.plan_label+" · "+(v.revoked?"ОТКЛЮЧЕН":v.used?"АКТИВИРОВАН":"НЕ ИСПОЛЬЗОВАН")+" · "+(v.expires_at||"без срока")+" <button data-id='"+v.id+"'>Отключить</button></pre>").join("");}catch(e){$("result").textContent=e.message}}
$("list").onclick=async e=>{if(e.target.dataset.id&&confirm("Отключить лицензию?")){try{await api("/admin/revoke",{id:e.target.dataset.id});await load()}catch(err){$("result").textContent=err.message}}};
</script></html>""",content_type="text/html; charset=utf-8")

@app.post("/admin/<action>")
def admin(action):
    if not admin_ok(): return jsonify(error="Неверный ключ администратора"),401
    body=request.get_json(silent=True)
    if not isinstance(body,dict): return jsonify(error="Invalid JSON"),400
    try:
        init_db()
        with db() as c:
            if action=="codes":
                plan=body.get("plan")
                if plan not in PLANS: return jsonify(error="Неизвестный тариф"),400
                code=secrets.token_hex(16).upper()
                lid=str(uuid.uuid4())
                c.execute("INSERT INTO ragestars_licenses(id,code_hash,code_hint,plan) VALUES(%s,%s,%s,%s)",(lid,digest(code),code[-6:],plan))
                return jsonify(id=lid,code=code,plan=plan,plan_label=PLANS[plan])
            if action=="list":
                rows=c.execute("""SELECT id,code_hint,plan,created_at,activated_at,expires_at,revoked,
                    (installation_hash IS NOT NULL) AS used FROM ragestars_licenses ORDER BY created_at DESC LIMIT 300""").fetchall()
                return jsonify(licenses=[{**dict(r),"id":str(r["id"]),"created_at":r["created_at"].isoformat(),
                    "activated_at":r["activated_at"].isoformat() if r["activated_at"] else None,
                    "expires_at":r["expires_at"].isoformat() if r["expires_at"] else None,
                    "plan_label":PLANS[r["plan"]]} for r in rows])
            if action=="revoke":
                try: lid=uuid.UUID(body.get("id",""))
                except Exception: return jsonify(error="Invalid ID"),400
                row=c.execute("UPDATE ragestars_licenses SET revoked=true WHERE id=%s RETURNING id",(lid,)).fetchone()
                return jsonify(revoked=bool(row))
            return jsonify(error="Not found"),404
    except Exception:
        app.logger.exception("admin endpoint failed")
        return jsonify(error="Ошибка сервера/БД"),503

@app.post("/activate")
def activate():
    body=request.get_json(silent=True)
    if not isinstance(body,dict): return jsonify(error="Invalid JSON"),400
    code=body.get("code"); installation=body.get("installation_id")
    if not isinstance(code,str) or not re.fullmatch(r"[A-F0-9]{32}",code): return jsonify(error="Неверный код"),400
    if not isinstance(installation,str) or not 20<=len(installation)<=128: return jsonify(error="Неверный ID установки"),400
    ih=digest(installation)
    try:
        init_db()
        with db() as c:
            row=c.execute("SELECT * FROM ragestars_licenses WHERE code_hash=%s FOR UPDATE",(digest(code),)).fetchone()
            if not row or row["revoked"] or row["installation_hash"] not in (None,ih):
                return jsonify(error="Код неверный, отключён или уже использован"),403
            now=c.execute("SELECT clock_timestamp() AS t").fetchone()["t"]
            activated=row["activated_at"] or now
            exp=row["expires_at"] or expiry(activated,row["plan"])
            if exp and exp<=now: return jsonify(error="Срок лицензии истёк",reason="expired"),403
            c.execute("UPDATE ragestars_licenses SET installation_hash=%s,activated_at=%s,expires_at=%s WHERE id=%s",(ih,activated,exp,row["id"]))
            return jsonify(token=token_for(str(row["id"]),ih),license_id=str(row["id"]),plan=row["plan"],expires_at=exp.isoformat() if exp else None)
    except Exception:
        app.logger.exception("activation failed")
        return jsonify(error="Ошибка сервера"),503

@app.post("/check")
def check():
    body=request.get_json(silent=True)
    if not isinstance(body,dict): return jsonify(active=False),400
    installation=body.get("installation_id"); lid=body.get("license_id"); token=body.get("token")
    if not isinstance(installation,str) or not 20<=len(installation)<=128 or not isinstance(lid,str) or not isinstance(token,str):
        return jsonify(active=False),400
    ih=digest(installation)
    try:
        init_db()
        with db() as c:
            row=c.execute("""SELECT plan,expires_at,revoked FROM ragestars_licenses WHERE id=%s AND installation_hash=%s""",(lid,ih)).fetchone()
            valid=hmac.compare_digest(token_for(lid,ih),token)
            if not row or not valid or row["revoked"]: return jsonify(active=False),403
            if row["expires_at"] and row["expires_at"]<=datetime.now(timezone.utc): return jsonify(active=False,reason="expired"),403
            return jsonify(active=True,plan=row["plan"],expires_at=row["expires_at"].isoformat() if row["expires_at"] else None)
    except Exception:
        app.logger.exception("license check failed")
        return jsonify(active=False),503

try:
    init_db()
except Exception:
    app.logger.exception("database initialization deferred")

if __name__=="__main__":
    init_db()
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","5000")))
