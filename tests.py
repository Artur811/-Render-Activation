import os,unittest
from unittest.mock import patch
import app
class Cursor:
 def __init__(self,row=None,rows=None,n=0):self.row=row;self.rows=rows;self.rowcount=n
 def fetchone(self):return self.row
 def fetchall(self):return self.rows
class DB:
 def __init__(self):self.rows={}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def execute(self,sql,args=()):
  if sql.startswith('INSERT'):
   self.rows[args[0]]={'id':args[0],'code_hash':args[1],'installation_hash':None,'revoked':False};return Cursor()
  if sql.startswith('UPDATE licenses SET installation_hash'):
   ih,code,other=args
   for r in self.rows.values():
    if r['code_hash']==code and not r['revoked'] and r['installation_hash'] in (None,other):r['installation_hash']=ih;return Cursor({'id':r['id']})
   return Cursor()
  if sql.startswith('SELECT id FROM'):
   r=self.rows.get(args[0]);return Cursor({'id':r['id']} if r and not r['revoked'] and r['installation_hash']==args[1] else None)
  if sql.startswith('UPDATE licenses SET revoked'):
   r=self.rows.get(args[0])
   if r:r['revoked']=True
   return Cursor(n=int(bool(r)))
  if sql.startswith('SELECT id,created_at'):return Cursor(rows=list(self.rows.values()))
  raise AssertionError(sql)
class Tests(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,{'ADMIN_SECRET':'test-admin','TOKEN_SECRET':'test-token','DATABASE_URL':'mock'});self.env.start()
  self.db=DB();self.mock=patch.object(app,'connect',return_value=self.db);self.mock.start();self.c=app.app.test_client()
 def tearDown(self):self.mock.stop();self.env.stop()
 def post(self,url,data,admin=False):return self.c.post(url,json=data,headers={'Authorization':'Bearer test-admin'} if admin else {})
 def test_full_flow(self):
  self.assertEqual(self.post('/admin/create',{}).status_code,401)
  issued=self.post('/admin/create',{},True).json
  first=self.post('/activate',{'code':issued['code'],'installation_id':'a'*32});self.assertEqual(first.status_code,200)
  retry=self.post('/activate',{'code':issued['code'],'installation_id':'a'*32});self.assertEqual(first.json,retry.json)
  self.assertEqual(self.post('/activate',{'code':issued['code'],'installation_id':'b'*32}).status_code,403)
  credentials={**first.json,'installation_id':'a'*32}
  self.assertTrue(self.post('/verify',credentials).json['active'])
  self.assertEqual(self.post('/verify',{**credentials,'token':'0'*64}).status_code,403)
  self.post('/admin/revoke',{'id':issued['id']},True)
  self.assertEqual(self.post('/verify',credentials).status_code,403)
 def test_fail_closed(self):
  with patch.dict(os.environ,{'TOKEN_SECRET':''}):self.assertEqual(self.post('/activate',{}).status_code,503)
 def test_bad_input(self):self.assertEqual(self.post('/activate',{'code':'x'}).status_code,400)
if __name__=='__main__':unittest.main(verbosity=2)
