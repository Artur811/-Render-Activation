import os, secrets, hashlib, hmac, uuid
from flask import Flask, request, jsonify, Response
import psycopg
from psycopg.rows import dict_row
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=4096
UI='<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Коды активации</title><style>body{font:18px system-ui;max-width:760px;margin:40px auto;padding:20px;background:#101827;color:#eef}input,button{font:inherit;padding:12px;margin:6px 0;max-width:95%}input{width:650px}pre{white-space:pre-wrap;overflow-wrap:anywhere}button{cursor:pointer}</style><h1>Одноразовые коды</h1><p>Это панель сервера, НЕ защита, уже встроенная в игру.</p><label>Ключ администратора<input id="key" type="password" autocomplete="off"></label><p><button id="create">Создать код</button> <button id="list">Список активаций</button></p><label>ID лицензии для отключения<input id="license"></label><button id="revoke">Отключить лицензию</button><pre id="out"></pre><script>async function api(path,data){try{const r=await fetch(path,{method:\'POST\',headers:{\'Content-Type\':\'application/json\',\'Authorization\':\'Bearer \'+document.getElementById(\'key\').value},body:JSON.stringify(data||{})});document.getElementById(\'out\').textContent=JSON.stringify(await r.json(),null,2)}catch(e){document.getElementById(\'out\').textContent=String(e)}}document.getElementById(\'create\').onclick=()=>api(\'/admin/create\');document.getElementById(\'list\').onclick=()=>api(\'/admin/list\');document.getElementById(\'revoke\').onclick=()=>api(\'/admin/revoke\',{id:document.getElementById(\'license\').value});</script>'
SCHEMA="""CREATE TABLE IF NOT EXISTS licenses (
id TEXT PRIMARY KEY,code_hash TEXT UNIQUE NOT NULL,installation_hash TEXT,
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), activated_at TIMESTAMPTZ,
revoked BOOLEAN NOT NULL DEFAULT FALSE)"""
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def connect():
 return psycopg.connect(os.environ['DATABASE_URL'],row_factory=dict_row)
def token(ident,ih):
 return hmac.new(os.environ['TOKEN_SECRET'].encode(),(ident+':'+ih).encode(),hashlib.sha256).hexdigest()
@app.after_request
def headers(r):
 r.headers['Cache-Control']='no-store'
 r.headers['X-Content-Type-Options']='nosniff'
 r.headers['X-Frame-Options']='DENY'
 r.headers['Referrer-Policy']='no-referrer'
 return r
@app.get('/')
def home(): return Response(UI,content_type='text/html; charset=utf-8')
@app.get('/health')
def health(): return jsonify(status='running')
@app.post('/<path:path>')
def api(path):
 if not all(os.environ.get(x) for x in ('DATABASE_URL','ADMIN_SECRET','TOKEN_SECRET')):
  return jsonify(error='Server not configured'),503
 if path.startswith('admin/') and not hmac.compare_digest(digest(request.headers.get('Authorization','')),digest('Bearer '+os.environ['ADMIN_SECRET'])):
  return jsonify(error='Unauthorized'),401
 b=request.get_json(silent=True)
 if not isinstance(b,dict): return jsonify(error='Invalid JSON'),400
 try:
  with connect() as c:
   if path=='admin/create':
    code=secrets.token_hex(24);ident=str(uuid.uuid4())
    c.execute('INSERT INTO licenses(id,code_hash) VALUES(%s,%s)',(ident,digest(code)))
    return jsonify(id=ident,code=code,note='Сохраните код: он показывается один раз.')
   if path=='admin/list':
    rows=c.execute('SELECT id,created_at,activated_at,revoked,(installation_hash IS NOT NULL) AS used FROM licenses ORDER BY created_at DESC LIMIT 100').fetchall()
    return jsonify(results=rows)
   if path=='admin/revoke':
    if not isinstance(b.get('id'),str):return jsonify(error='Missing id'),400
    r=c.execute('UPDATE licenses SET revoked=TRUE WHERE id=%s',(b['id'],))
    return jsonify(changed=r.rowcount)
   if path in ('activate','verify'):
    installation=b.get('installation_id')
    if not isinstance(installation,str) or not 20<=len(installation)<=128:return jsonify(error='Invalid installation_id'),400
    ih=digest(installation)
    if path=='activate':
     code=b.get('code')
     if not isinstance(code,str) or len(code)!=48:return jsonify(error='Invalid code'),400
     row=c.execute('UPDATE licenses SET installation_hash=%s,activated_at=COALESCE(activated_at,NOW()) WHERE code_hash=%s AND revoked=FALSE AND (installation_hash IS NULL OR installation_hash=%s) RETURNING id',(ih,digest(code),ih)).fetchone()
     if not row:return jsonify(error='Код неверный, отключён или использован другой установкой'),403
     return jsonify(license_id=row['id'],token=token(row['id'],ih))
    ident=b.get('license_id');received=b.get('token')
    if not isinstance(ident,str) or not isinstance(received,str) or len(received)!=64:return jsonify(error='Invalid fields'),400
    row=c.execute('SELECT id FROM licenses WHERE id=%s AND installation_hash=%s AND revoked=FALSE',(ident,ih)).fetchone()
    active=bool(row) and hmac.compare_digest(digest(token(ident,ih)),digest(received))
    return jsonify(active=active),200 if active else 403
   return jsonify(error='Not found'),404
 except Exception:
  app.logger.exception('Database request failed')
  return jsonify(error='Database unavailable'),503
if __name__=='__main__':
 import sys
 if '--init-db' in sys.argv:
  with connect() as c:c.execute(SCHEMA)
 else:app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')))
