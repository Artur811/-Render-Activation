import os
import secrets
import hashlib
import hmac
import uuid
import base64
import calendar
import re
import threading
from datetime import timedelta, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from flask import Flask, request, jsonify, Response
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4096

UI = r'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0b0d12">
<title>AUTHGUARD — Generated Keys</title>
<style>
:root{color-scheme:dark;--bg:#0b0d12;--side:#080a0e;--surface:#12151d;--surface2:#191d27;--line:#272c38;--muted:#9299aa;--text:#f3f5fa;--purple:#7b3ff2;--purple2:#6326d9;--blue:#3478f6;--green:#1dbb83;--red:#e34d58;--amber:#d99a35}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;min-height:100vh}
button,input,select{font:inherit}button{cursor:pointer;border:0}.hidden{display:none!important}
.login-wrap{min-height:100vh;display:grid;place-items:center;padding:22px;background:radial-gradient(ellipse at 50% 15%,#28203f 0%,#11131b 42%,#0b0d12 78%)}
.login-card{width:min(100%,390px);background:#141720;border:1px solid #303444;border-radius:16px;padding:28px;box-shadow:0 25px 90px #0009}.brand-mark{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#8d5aff,#5520c4);display:grid;place-items:center;font-weight:900;font-size:19px;box-shadow:0 8px 22px #6c36df55}.login-brand{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.09em}.login-card h1{font-size:23px;margin:28px 0 7px}.sub{color:var(--muted);line-height:1.55;margin:0 0 23px}.field-label{display:block;color:#c5c9d4;font-size:12px;font-weight:650;margin:0 0 8px}.text-input,.select-input{width:100%;height:43px;border:1px solid #303644;border-radius:8px;background:#0d1017;color:#f7f8fb;padding:0 13px;outline:none}.text-input:focus,.select-input:focus{border-color:#8255e9;box-shadow:0 0 0 3px #8255e922}.primary{background:linear-gradient(135deg,var(--purple),var(--purple2));color:white;border-radius:8px;padding:11px 17px;font-weight:700;box-shadow:0 4px 14px #6428cb33}.primary:hover{filter:brightness(1.12)}.login-card .primary{width:100%;margin-top:15px;height:44px}.error{min-height:20px;color:#ff7b83;font-size:12px;margin-top:12px}
.app-shell{min-height:100vh;display:grid;grid-template-columns:218px minmax(0,1fr)}
.sidebar{background:var(--side);border-right:1px solid #1d212b;padding:23px 14px;display:flex;flex-direction:column;min-height:100vh}.side-brand{display:flex;align-items:center;gap:10px;padding:0 9px 30px;font-weight:850;letter-spacing:.08em;font-size:14px}.side-brand .brand-mark{width:31px;height:31px;font-size:15px;border-radius:9px}.nav-title{font-size:10px;text-transform:uppercase;color:#626a7a;letter-spacing:.12em;padding:0 10px 9px}.nav-link{display:flex;align-items:center;gap:11px;color:#aeb4c2;text-decoration:none;padding:11px 12px;border-radius:8px;margin:2px 0;font-size:12px;font-weight:650}.nav-link.active{background:#27183e;color:#c9aaff;box-shadow:inset 2px 0 #965cff}.nav-icon{width:17px;text-align:center;font-size:15px}.sidebar-bottom{margin-top:auto}.server-status{display:flex;align-items:center;gap:8px;color:#8e97a8;font-size:11px;padding:12px 10px;border-top:1px solid #1e222c;margin-bottom:5px}.dot{width:7px;height:7px;background:var(--green);border-radius:50%;box-shadow:0 0 9px #1dbb8366}.logout{width:100%;text-align:left;background:transparent;color:#aab0be;padding:11px 10px;border-radius:7px;font-size:12px}.logout:hover{background:#191c25;color:#fff}
.main{min-width:0;padding:31px clamp(18px,3.2vw,48px) 45px}.topline{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:26px}.eyebrow{color:#9a79da;font-weight:750;font-size:10px;letter-spacing:.13em;text-transform:uppercase;margin-bottom:8px}.heading{font-size:25px;font-weight:800;letter-spacing:-.03em;margin:0 0 6px}.description{color:var(--muted);font-size:12px;margin:0}.create-btn{display:inline-flex;align-items:center;gap:9px;white-space:nowrap;height:40px}.plus{font-size:19px;line-height:12px;font-weight:400}
.card{background:var(--surface);border:1px solid var(--line);border-radius:11px;overflow:hidden}.toolbar{padding:15px;display:grid;grid-template-columns:minmax(180px,1fr) 175px 115px auto;gap:10px;border-bottom:1px solid var(--line)}.search-wrap{position:relative}.search-wrap span{position:absolute;left:12px;top:12px;color:#727b8d}.search-wrap input{padding-left:35px}.select-input{height:41px;font-size:12px}.toolbar-btn{height:41px;padding:0 14px;border:1px solid #333948;background:#202431;color:#c6cbd5;border-radius:8px;font-size:12px;font-weight:700}.toolbar-btn:hover{border-color:#7551bd;color:#fff}
.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:700px}thead{background:#1a1e28}th{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:#a4abba;text-align:left;padding:13px 14px;font-weight:750;white-space:nowrap}td{padding:13px 14px;border-top:1px solid #252a35;color:#d8dbe3;font-size:11px;white-space:nowrap}tbody tr:hover{background:#171b24}.key-cell{font-family:ui-monospace,SFMono-Regular,monospace;color:#c9b5ff;letter-spacing:.02em}.muted{color:var(--muted)}.status{display:inline-flex;align-items:center;gap:6px;border-radius:20px;padding:5px 9px;font-size:10px;font-weight:750}.status:before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor}.status.unused{background:#15372d;color:#54d6a5}.status.used{background:#202f50;color:#85b2ff}.status.revoked{background:#44232a;color:#ff8790}.actions{display:flex;gap:6px}.mini-btn{padding:7px 9px;border-radius:6px;color:#e8e1ff;background:#392064;font-size:10px;font-weight:700}.mini-btn:hover{filter:brightness(1.2)}.mini-btn.danger{background:#49242b;color:#ff9da3}.empty{padding:42px 15px;text-align:center;color:#828b9d;font-size:12px}.table-foot{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:13px 15px;color:#8e96a6;font-size:11px;border-top:1px solid var(--line)}.refresh{border:0;background:transparent;color:#bba2f3;font-weight:700;font-size:11px}
.notice{color:#858ea0;font-size:11px;line-height:1.5;margin:13px 2px 0}.modal-backdrop{position:fixed;inset:0;background:#000a;display:grid;place-items:center;padding:20px;z-index:5}.modal{width:min(100%,480px);background:#161a24;border:1px solid #373d4d;border-radius:14px;padding:22px;box-shadow:0 25px 80px #000b}.modal-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.modal h2{font-size:18px;margin:0}.close{background:#272c37;border-radius:7px;color:#cbd0da;width:30px;height:30px;font-size:18px}.modal p{color:#a2aabb;font-size:12px;line-height:1.5}.new-code{padding:15px;background:#0d1119;border:1px dashed #67509b;border-radius:9px;color:#d8c9ff;font:700 14px ui-monospace,monospace;overflow-wrap:anywhere;line-height:1.6;margin:14px 0}.modal-actions{display:flex;gap:9px}.modal-actions button{flex:1}.secondary{background:#292e3a;color:#d8dce5;border-radius:8px;padding:11px 14px;font-weight:700}.toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);background:#202735;border:1px solid #424b5e;color:#edf0f7;border-radius:9px;padding:10px 15px;font-size:12px;box-shadow:0 8px 30px #0008;z-index:10}
@media(max-width:850px){.app-shell{grid-template-columns:1fr}.sidebar{min-height:auto;padding:12px 14px 8px;border-right:0;border-bottom:1px solid #1d212b}.side-brand{padding:0 5px 10px}.nav-title,.sidebar-bottom{display:none}.nav-link{display:inline-flex;margin:0 4px 0 0;padding:9px 11px}.sidebar nav{display:flex;overflow-x:auto}.main{padding-top:23px}.toolbar{grid-template-columns:1fr 1fr}.search-wrap{grid-column:1/-1}.toolbar-btn{grid-column:auto}}
@media(max-width:520px){.main{padding:19px 12px 32px}.topline{align-items:center;flex-direction:column}.topline>div{width:100%}.create-btn{width:100%;justify-content:center}.heading{font-size:22px}.toolbar{grid-template-columns:1fr 1fr;padding:11px}.toolbar-btn{width:100%}.table-foot{align-items:flex-start;flex-direction:column}.login-card{padding:23px}}

.create-tools{display:flex;align-items:flex-end;gap:10px;flex-wrap:wrap}.plan-picker{min-width:195px}.plan-picker .field-label{margin-bottom:5px}.plan-picker select{height:40px}.status.expired{background:#49351b;color:#ffd078}.expiry-cell{white-space:normal;min-width:140px;line-height:1.5}.tariff-notice{padding:12px 15px;border-top:1px solid var(--line);color:#a5b4d1;font-size:11px;line-height:1.6}@media(max-width:520px){.create-tools{width:100%}.plan-picker{width:100%}.create-tools .create-btn{width:100%}}
</style>
</head>
<body>
<section class="login-wrap" id="loginScreen">
  <div class="login-card">
    <div class="login-brand"><div class="brand-mark">A</div><span>AUTHGUARD</span></div>
    <h1>Вход в панель</h1>
    <p class="sub">Введите личный пароль администратора, чтобы открыть генератор кодов.</p>
    <label class="field-label" for="password">ADMINISTRATOR PASSWORD</label>
    <input class="text-input" id="password" type="password" autocomplete="current-password" placeholder="Пароль администратора">
    <button class="primary" id="loginBtn">Войти в панель</button>
    <div class="error" id="loginError" role="alert"></div>
  </div>
</section>
<div class="app-shell hidden" id="appScreen">
  <aside class="sidebar">
    <div class="side-brand"><div class="brand-mark">A</div><span>AUTHGUARD</span></div>
    <div class="nav-title">УПРАВЛЕНИЕ</div>
    <nav><a class="nav-link active" href="#generated"><span class="nav-icon">🔑</span>Generated Keys</a></nav>
    <div class="sidebar-bottom">
      <div class="server-status"><span class="dot"></span>Сервер подключён</div>
      <button class="logout" id="logoutBtn">↪ Выйти</button>
    </div>
  </aside>
  <main class="main" id="generated">
    <header class="topline">
      <div><div class="eyebrow">AUTHGUARD / LICENSE TOOLS</div><h1 class="heading">Generated Keys</h1><p class="description">Создание и просмотр одноразовых кодов активации</p></div>
      <div class="create-tools"><div class="plan-picker"><label class="field-label" for="plan">ТАРИФ НОВОГО КОДА</label><select class="select-input" id="plan"><option value="week">1 неделя · 7 суток</option><option value="month">1 календарный месяц</option></select></div><button class="primary create-btn" id="createBtn"><span class="plus">＋</span>Сгенерировать код</button></div>
    </header>
    <section class="card">
      <div class="toolbar">
        <div class="search-wrap"><span>⌕</span><input class="text-input" id="search" placeholder="Поиск по коду или ID лицензии" aria-label="Поиск"></div>
        <select class="select-input" id="statusFilter" aria-label="Фильтр по статусу"><option value="all">Все коды</option><option value="unused">Не использованы</option><option value="used">Активированы</option><option value="expired">Срок истёк</option><option value="revoked">Отключены</option></select>
        <select class="select-input" id="pageSize" aria-label="Количество строк"><option value="10">10 строк</option><option value="25" selected>25 строк</option><option value="50">50 строк</option><option value="100">100 строк</option></select>
        <button class="toolbar-btn" id="refreshBtn">↻ Обновить</button>
      </div>
      <div class="table-wrap"><table><thead><tr><th>Код / метка</th><th>Тариф</th><th>Создан</th><th>Доступ до</th><th>Статус</th><th>Устройство</th><th>Действия</th></tr></thead><tbody id="rows"><tr><td colspan="7" class="empty">Загружаем коды…</td></tr></tbody></table></div>
      <div class="table-foot"><span id="rowCount">—</span><span>Даты показаны в часовом поясе вашего браузера.</span></div>
    <div class="tariff-notice">Срок начинается с первой активации, а не с генерации кода. Неделя — 7 суток; месяц — календарный (расчёт по UTC). Старые коды сохраняют прежний доступ без срока: при необходимости отключите их и выдайте новые.</div></section>
    <p class="notice">Одноразовый код привязывается к первому устройству, которое успешно его активирует. После этого другой установке он не подойдёт.</p>
  </main>
</div>
<div class="modal-backdrop hidden" id="codeModal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
  <div class="modal"><div class="modal-head"><h2 id="modalTitle">Новый код создан</h2><button class="close" id="closeModal" aria-label="Закрыть">×</button></div><p>Передайте код пользователю. Срок выбранного тарифа начнётся при его первой успешной активации.</p><p id="newPlan" style="color:#c9b5ff;font-weight:700"></p><div class="new-code" id="newCode"></div><div class="modal-actions"><button class="primary" id="copyCode">Скопировать код</button><button class="secondary" id="doneCode">Готово</button></div></div>
</div>
<div class="toast hidden" id="toast" role="status"></div>
<script>
let adminSecret='';let allRows=[];let newCodeValue='';
const $=id=>document.getElementById(id);
function toast(message){const el=$('toast');el.textContent=message;el.classList.remove('hidden');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>el.classList.add('hidden'),2600)}
async function api(path,data={}){const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+adminSecret},body:JSON.stringify(data)});let result={};try{result=await response.json()}catch(_e){}if(!response.ok){const message=response.status===401?'Неверный пароль администратора.':(result.error||'Ошибка запроса.');throw new Error(message)}return result}
function esc(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function statusOf(row){if(row.revoked)return 'revoked';if(row.expired||(row.expires_at&&Date.parse(row.expires_at)<=Date.now()))return 'expired';return row.used?'used':'unused'}
function formatDate(value){if(!value)return '—';const date=new Date(value);return isNaN(date)?'—':date.toLocaleString('ru-RU',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'})}
function render(){const q=$('search').value.trim().toLowerCase();const filter=$('statusFilter').value;const size=Number($('pageSize').value);const filtered=allRows.filter(row=>{const st=statusOf(row);const text=[row.id,row.code_hint,row.code].join(' ').toLowerCase();return (!q||text.includes(q))&&(filter==='all'||st===filter)});const shown=filtered.slice(0,size);$('rowCount').textContent=`Показано ${shown.length} из ${filtered.length} записей`;
if(!shown.length){$('rows').innerHTML='<tr><td colspan="7" class="empty">Коды не найдены. Нажмите «Сгенерировать код», чтобы создать первый.</td></tr>';return}
$('rows').innerHTML=shown.map(row=>{const st=statusOf(row);const label=st==='revoked'?'Отключён':st==='expired'?'Срок истёк':st==='used'?'Активирован':'Не использован';const key=row.code?esc(row.code):(row.code_hint?`••••••${esc(row.code_hint)}`:`Старый код · ${esc(String(row.id).slice(0,8))}`);const device=row.used?'Привязан':'Не задан';return `<tr><td><span class="key-cell">${key}</span><div class="muted" style="font-size:9px;margin-top:4px">ID: ${esc(String(row.id).slice(0,8))}</div></td><td>${esc(row.plan_label||"Старый код · без срока")}</td><td>${esc(formatDate(row.created_at))}</td><td class="expiry-cell">${row.expires_at?esc(formatDate(row.expires_at)):(row.plan==='legacy'?'Без срока':'Отсчёт после активации')}</td><td><span class="status ${st}">${label}</span></td><td>${device}</td><td><div class="actions">${row.code?`<button class="mini-btn" data-copy="${esc(row.id)}">Копировать</button>`:''}<button class="mini-btn" data-detail="${esc(row.id)}">Подробнее</button>${st!=='revoked'?`<button class="mini-btn danger" data-revoke="${esc(row.id)}">Отключить</button>`:''}</div></td></tr>`}).join('');
}
async function loadRows(){ $('rows').innerHTML='<tr><td colspan="7" class="empty">Загружаем коды…</td></tr>';try{const data=await api('/admin/list');allRows=data.results||[];render()}catch(e){$('rows').innerHTML=`<tr><td colspan="7" class="empty">${esc(e.message)}</td></tr>`;toast(e.message)}}
async function login(){const val=$('password').value.trim();if(!val){$('loginError').textContent='Введите пароль.';return}$('loginBtn').disabled=true;$('loginError').textContent='Проверяем доступ…';adminSecret=val;try{const data=await api('/admin/list');allRows=data.results||[];$('loginScreen').classList.add('hidden');$('appScreen').classList.remove('hidden');$('loginError').textContent='';$('password').value='';render()}catch(e){adminSecret='';$('loginError').textContent=e.message;$('password').focus()}finally{$('loginBtn').disabled=false}}
async function createKey(){const btn=$('createBtn');btn.disabled=true;try{const data=await api('/admin/create',{plan:$('plan').value});$('newPlan').textContent='Тариф: '+data.plan_label+' · отсчёт после активации';newCodeValue=data.code;$('newCode').textContent=newCodeValue;$('codeModal').classList.remove('hidden');await loadRows()}catch(e){toast(e.message)}finally{btn.disabled=false}}
function closeModal(){$('codeModal').classList.add('hidden');newCodeValue=''}
$('loginBtn').addEventListener('click',login);$('password').addEventListener('keydown',e=>{if(e.key==='Enter')login()});$('logoutBtn').addEventListener('click',()=>{adminSecret='';allRows=[];$('appScreen').classList.add('hidden');$('loginScreen').classList.remove('hidden');$('password').value='';$('password').focus()});$('createBtn').addEventListener('click',createKey);$('refreshBtn').addEventListener('click',loadRows);$('search').addEventListener('input',render);$('statusFilter').addEventListener('change',render);$('pageSize').addEventListener('change',render);$('closeModal').addEventListener('click',closeModal);$('doneCode').addEventListener('click',closeModal);$('copyCode').addEventListener('click',async()=>{try{await navigator.clipboard.writeText(newCodeValue);toast('Код скопирован')}catch(_e){toast('Скопируйте код вручную')} });
$('rows').addEventListener('click',async e=>{const copy=e.target.closest('[data-copy]');const detail=e.target.closest('[data-detail]');const revoke=e.target.closest('[data-revoke]');if(copy){const row=allRows.find(r=>r.id===copy.dataset.copy);if(row?.code){try{await navigator.clipboard.writeText(row.code);toast('Код скопирован')}catch(_e){toast('Не удалось скопировать код')}}}if(detail){const row=allRows.find(r=>r.id===detail.dataset.detail);if(row)toast(`ID: ${row.id} · Создан: ${formatDate(row.created_at)} · Активация: ${formatDate(row.activated_at)} · Тариф: ${row.plan_label||"Без срока"} · Доступ до: ${row.expires_at?formatDate(row.expires_at):"—"}`)}if(revoke&&confirm('Отключить этот код? После этого активировать его будет нельзя.')){try{await api('/admin/revoke',{id:revoke.dataset.revoke});toast('Код отключён');await loadRows()}catch(err){toast(err.message)}}});
setInterval(()=>{if(adminSecret&&!$('appScreen').classList.contains('hidden'))render()},30000);
</script>
</body></html>'''

SCHEMA = """CREATE TABLE IF NOT EXISTS licenses (
    id TEXT PRIMARY KEY,
    code_hash TEXT UNIQUE NOT NULL,
    installation_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    revoked BOOLEAN NOT NULL DEFAULT FALSE
)"""

PLANS = {'week': '1 неделя', 'month': '1 календарный месяц', 'legacy': 'Старый код · без срока'}
_schema_ready = False
_schema_lock = threading.Lock()


def digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def connect():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise RuntimeError('DATABASE_URL is not configured')
    return psycopg.connect(database_url, row_factory=dict_row)


def ensure_schema(connection):
    # The transaction lock also serializes migrations across gunicorn workers.
    connection.execute('SELECT pg_advisory_xact_lock(748192603)')
    connection.execute(SCHEMA)
    connection.execute('ALTER TABLE licenses ADD COLUMN IF NOT EXISTS code_hint VARCHAR(8)')
    connection.execute('ALTER TABLE licenses ADD COLUMN IF NOT EXISTS code_encrypted TEXT')
    # No retroactive expiry: existing codes retain their previous access.
    connection.execute("ALTER TABLE licenses ADD COLUMN IF NOT EXISTS plan VARCHAR(16) NOT NULL DEFAULT 'legacy'")
    connection.execute('ALTER TABLE licenses ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ')


def ensure_database():
    global _schema_ready
    if _schema_ready:
        return
    with _schema_lock:
        if not _schema_ready:
            with connect() as connection:
                ensure_schema(connection)
            # Mark ready only after the migration transaction committed.
            _schema_ready = True


def expiration_for(start, plan):
    """An elapsed UTC week or one calendar month from FIRST activation."""
    if start.tzinfo is None:
        raise ValueError('Activation timestamp must be timezone-aware')
    start = start.astimezone(timezone.utc)
    if plan == 'legacy':
        return None
    if plan == 'week':
        return start + timedelta(days=7)
    if plan == 'month':
        year, month = start.year + (start.month == 12), start.month % 12 + 1
        day = min(start.day, calendar.monthrange(year, month)[1])
        return start.replace(year=year, month=month, day=day)
    raise ValueError('Unknown plan')


def admin_authorized() -> bool:
    secret = os.environ.get('ADMIN_SECRET', '')
    supplied = request.headers.get('Authorization', '')
    return bool(secret) and hmac.compare_digest(digest(supplied), digest('Bearer ' + secret))


def encryption_key() -> bytes:
    secret = os.environ.get('TOKEN_SECRET', '').encode('utf-8')
    if not secret:
        raise RuntimeError('TOKEN_SECRET is not configured')
    return hashlib.sha256(b'AUTHGUARD-CODE-ENCRYPTION-v1:' + secret).digest()


def encrypt_code(code: str) -> str:
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(encryption_key()).encrypt(nonce, code.encode('utf-8'), b'AUTHGUARD')
    return base64.urlsafe_b64encode(nonce + ciphertext).decode('ascii')


def decrypt_code(value: str | None) -> str | None:
    if not value:
        return None
    raw = base64.urlsafe_b64decode(value.encode('ascii'))
    return AESGCM(encryption_key()).decrypt(raw[:12], raw[12:], b'AUTHGUARD').decode('utf-8')


def make_token(license_id: str, installation_hash: str) -> str:
    secret = os.environ.get('TOKEN_SECRET', '')
    if not secret:
        raise RuntimeError('TOKEN_SECRET is not configured')
    return hmac.new(secret.encode('utf-8'), (license_id + ':' + installation_hash).encode('utf-8'), hashlib.sha256).hexdigest()


def iso(value):
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


@app.after_request
def add_security_headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response


@app.get('/')
def home():
    return Response(UI, content_type='text/html; charset=utf-8')


@app.get('/health')
def health():
    return jsonify(status='running', version='tariffs-1')


@app.post('/<path:path>')
def api(path):
    admin_routes = {'admin/create', 'admin/list', 'admin/revoke'}
    if path in admin_routes:
        if not all(os.environ.get(n) for n in ('DATABASE_URL', 'ADMIN_SECRET', 'TOKEN_SECRET')):
            return jsonify(error='Сервер не настроен: проверьте переменные Render.'), 503
        if not admin_authorized():
            return jsonify(error='Неверный пароль администратора.'), 401
    elif path in ('activate', 'verify'):
        if not all(os.environ.get(n) for n in ('DATABASE_URL', 'TOKEN_SECRET')):
            return jsonify(error='Server not configured'), 503
    else:
        return jsonify(error='Not found'), 404

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error='Invalid JSON'), 400

    try:
        ensure_database()
        with connect() as connection:
            if path == 'admin/create':
                plan = body.get('plan')
                if not isinstance(plan, str) or plan not in ('week', 'month'):
                    return jsonify(error='Выберите тариф: 1 неделя или 1 календарный месяц.'), 400
                code = secrets.token_hex(24)
                license_id = str(uuid.uuid4())
                connection.execute(
                    '''INSERT INTO licenses(id, code_hash, code_hint, code_encrypted, plan)
                       VALUES (%s, %s, %s, %s, %s)''',
                    (license_id, digest(code), code[-8:], encrypt_code(code), plan)
                )
                return jsonify(id=license_id, code=code, plan=plan, plan_label=PLANS[plan],
                               expires_at=None, note='Отсчёт начнётся при первой активации кода.')

            if path == 'admin/list':
                rows = connection.execute(
                    '''SELECT id, code_hint, code_encrypted, created_at, activated_at, revoked,
                              plan, expires_at, (installation_hash IS NOT NULL) AS used,
                              (expires_at IS NOT NULL AND expires_at <= clock_timestamp()) AS expired
                       FROM licenses ORDER BY created_at DESC LIMIT 500'''
                ).fetchall()
                results = []
                for row in rows:
                    results.append({
                        'id': row['id'], 'code_hint': row['code_hint'],
                        'code': decrypt_code(row['code_encrypted']),
                        'created_at': iso(row['created_at']), 'activated_at': iso(row['activated_at']),
                        'revoked': bool(row['revoked']), 'used': bool(row['used']),
                        'plan': row['plan'], 'plan_label': PLANS.get(row['plan'], 'Неизвестный тариф'),
                        'expires_at': iso(row['expires_at']), 'expired': bool(row['expired']),
                    })
                return jsonify(results=results)

            if path == 'admin/revoke':
                license_id = body.get('id')
                if not isinstance(license_id, str) or not 1 <= len(license_id) <= 64:
                    return jsonify(error='Некорректный ID лицензии.'), 400
                result = connection.execute(
                    'UPDATE licenses SET revoked=TRUE WHERE id=%s AND revoked=FALSE RETURNING id',
                    (license_id,)
                ).fetchone()
                return jsonify(changed=1 if result else 0)

            installation = body.get('installation_id')
            if not isinstance(installation, str) or not 20 <= len(installation) <= 128:
                return jsonify(error='Invalid installation_id'), 400
            installation_hash = digest(installation)

            if path == 'activate':
                code = body.get('code')
                if not isinstance(code, str) or re.fullmatch(r'[0-9a-f]{48}', code) is None:
                    return jsonify(error='Invalid code'), 400
                # Row lock prevents two installations from claiming the same unused code.
                row = connection.execute(
                    'SELECT * FROM licenses WHERE code_hash=%s FOR UPDATE', (digest(code),)
                ).fetchone()
                if not row or row['revoked'] or row['installation_hash'] not in (None, installation_hash):
                    return jsonify(error='Код неверный, отключён или уже использован другой установкой.', reason='invalid'), 403
                # Read the actual database clock AFTER taking the row lock.
                now = connection.execute('SELECT clock_timestamp() AS now').fetchone()['now']
                activated_at = row['activated_at'] or now
                expires_at = row['expires_at']
                if expires_at is None and row['plan'] != 'legacy':
                    expires_at = expiration_for(activated_at, row['plan'])
                if expires_at is not None and expires_at <= now:
                    return jsonify(error='Срок доступа истёк. Получите новый код у администратора.',
                                   reason='expired', expires_at=iso(expires_at)), 403
                connection.execute(
                    '''UPDATE licenses SET installation_hash=%s, activated_at=%s, expires_at=%s
                       WHERE id=%s''',
                    (installation_hash, activated_at, expires_at, row['id'])
                )
                return jsonify(license_id=row['id'], token=make_token(row['id'], installation_hash),
                               plan=row['plan'], activated_at=iso(activated_at), expires_at=iso(expires_at))

            # Backward-compatible with the already distributed APK.
            license_id = body.get('license_id')
            received_token = body.get('token')
            if (not isinstance(license_id, str) or not 1 <= len(license_id) <= 64
                    or not isinstance(received_token, str)
                    or re.fullmatch(r'[0-9a-f]{64}', received_token) is None):
                return jsonify(error='Invalid fields'), 400
            row = connection.execute(
                '''SELECT id, plan, expires_at, revoked,
                          (expires_at IS NOT NULL AND expires_at <= clock_timestamp()) AS expired
                   FROM licenses WHERE id=%s AND installation_hash=%s''',
                (license_id, installation_hash)
            ).fetchone()
            token_valid = hmac.compare_digest(make_token(license_id, installation_hash), received_token)
            if not row or not token_valid or row['revoked']:
                return jsonify(active=False, reason='invalid'), 403
            # Fail closed for malformed limited plans without an expiration.
            if row['expired'] or (row['plan'] != 'legacy' and row['expires_at'] is None):
                return jsonify(active=False, reason='expired', expires_at=iso(row['expires_at'])), 403
            return jsonify(active=True, plan=row['plan'], expires_at=iso(row['expires_at']))

    except Exception:
        app.logger.exception('Request failed')
        return jsonify(error='Ошибка сервера или базы данных. Проверьте журналы Render.'), 503


if __name__ == '__main__':
    import sys
    if '--init-db' in sys.argv:
        ensure_database()
    else:
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '5000')))
