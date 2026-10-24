"""Build the deployable site into dist/.

Usage:  python3 build.py <password>

Family photos are read from photos/faces.json (kept out of git) and AES-GCM encrypted
with a key derived from the password, so they only appear after unlocking.
Without photos/faces.json the game still works, with emoji instead of photos."""
import base64, json, os, re, shutil, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

PASSWORD = sys.argv[1]
ITER = 250000
if len(sys.argv) < 2: sys.exit('usage: python3 build.py <password>')
src = open('game.html').read()
m = re.search(r"/\*FACES\*/(\{.*?\})/\*END\*/", src, re.S)
faces = open('photos/faces.json').read() if os.path.exists('photos/faces.json') else '{}'
os.makedirs('dist', exist_ok=True)

salt, iv = os.urandom(16), os.urandom(12)
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(PASSWORD.encode())
ct = AESGCM(key).encrypt(iv, faces.encode(), None)
b64 = lambda b: base64.b64encode(b).decode()
enc = json.dumps({'salt': b64(salt), 'iv': b64(iv), 'ct': b64(ct), 'iter': ITER})

s = src.replace(m.group(0), '/*FACES*/{}/*END*/')

css = """
.lock{position:fixed;inset:0;z-index:50;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:max(16px,env(safe-area-inset-top,0px)) max(16px,env(safe-area-inset-right,0px)) max(16px,env(safe-area-inset-bottom,0px)) max(16px,env(safe-area-inset-left,0px))}
.lock form{background:var(--white);border:4px solid var(--ink);border-radius:16px;box-shadow:0 6px 0 var(--ink);padding:24px;display:flex;flex-direction:column;gap:12px;align-items:center;width:min(360px,100%);text-align:center}
.lock h2{font-family:var(--display);font-weight:400;font-size:28px;margin:0;color:var(--ink)}
.lock .lockico{font-size:44px;line-height:1}
.lock input{font:800 18px var(--body);width:100%;box-sizing:border-box;padding:10px 12px;border:3px solid var(--ink);border-radius:10px;color:var(--ink);background:var(--key)}
.lock input:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.lock .err{color:var(--hot);font-weight:800;min-height:1.2em;margin:0}
"""
html = """<div class="lock" id="lock"><form id="lockForm" autocomplete="off">
<div class="lockico" aria-hidden="true">🔒</div><h2>Eliot's Power Keys</h2>
<label for="lockPw" style="font-weight:800">Grown-up password</label>
<input id="lockPw" type="password" autocomplete="current-password">
<button class="btn" type="submit">Unlock</button><p class="err" id="lockErr" role="alert"></p></form></div>
"""
js = """

/* ---------- cloud save (encrypted with the game password) ---------- */
let CK=null,CKEY=null,cloudT=null,lastPush=0,cloudDirtyFlag=false;
const cmsg=t=>{const el=document.getElementById('cloudMsg');if(el)el.textContent='☁️ '+t};
const b64e=u=>{let s='';for(let i=0;i<u.length;i+=8192)s+=String.fromCharCode.apply(null,u.subarray(i,i+8192));return btoa(s)};
const b64u=t=>Uint8Array.from(atob(t),c=>c.charCodeAt(0));
function snap(){const o={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);if(k&&k.startsWith('rt-')&&k!=='rt-pw')o[k]=localStorage.getItem(k)}return o}
async function cloudPush(force){if(!CK)return;const now=Date.now();if(!force&&now-lastPush<30000){clearTimeout(cloudT);cloudT=setTimeout(()=>cloudPush(true),30000-(now-lastPush));return}
  lastPush=now;cloudDirtyFlag=false;const u=String(now);localStorage.setItem('rt-updated',u);const data=snap();data['rt-updated']=u;
  try{const iv=crypto.getRandomValues(new Uint8Array(12));const ct=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv},CK,new TextEncoder().encode(JSON.stringify(data))));
    const all=new Uint8Array(12+ct.length);all.set(iv);all.set(ct,12);
    const r=await fetch('/api/save',{method:'PUT',keepalive:all.length<60000,headers:{'x-save-key':CKEY,'Content-Type':'text/plain'},body:b64e(all)});
    cmsg(r.ok?'Saved to the cloud at '+new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}):'Cloud save failed ('+r.status+'). Progress is still saved on this computer.')}
  catch(e){cmsg('Cloud save is offline. Progress is still saved on this computer.')}}
function mergeIn(data,cloudNewer){const J=(x,d)=>{try{return x==null?d:JSON.parse(x)}catch(e){return d}};let changed=false;
  const keepLocal=['rt-lang','rt-sound','rt-voice','rt-mine','rt-tab'];
  for(const k of Object.keys(data)){if(k==='rt-updated')continue;const cv=data[k],lv=localStorage.getItem(k);let nv=cv;
    if(keepLocal.includes(k)&&lv!=null)continue;
    const mergeable=['rt-stars','rt-words','rt-real','rt-found','rt-time','rt-unlock'].includes(k);if(!mergeable&&!cloudNewer&&lv!=null)continue;
    if(k==='rt-stars'||k==='rt-words'){const a=J(lv,{}),c=J(cv,{});for(const x in c)a[x]=Math.max(a[x]||0,c[x]);nv=JSON.stringify(a)}
    else if(k==='rt-real'||k==='rt-found'){const a=J(lv,{}),c=J(cv,{});for(const x in c)if(c[x])a[x]=c[x];nv=JSON.stringify(a)}
    else if(k==='rt-time'){const a=J(lv,{}),c=J(cv,{});for(const x in c)a[x]=Math.max(a[x]||0,c[x]);nv=JSON.stringify(a)}
    else if(k==='rt-unlock'){nv=JSON.stringify(J(lv,false)||J(cv,false))}
    if(nv!==lv){localStorage.setItem(k,nv);changed=true}}
  if(cloudNewer)localStorage.setItem('rt-updated',data['rt-updated']||String(Date.now()));return changed}
async function cloudPull(){try{const r=await fetch('/api/save',{headers:{'x-save-key':CKEY},cache:'no-store'});
    if(r.status===404){cmsg('Cloud save started.');return cloudPush(true)}
    if(!r.ok){cmsg('Cloud save not available ('+r.status+'). Progress is saved on this computer.');return}
    const u=b64u((await r.text()).trim());const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:u.slice(0,12)},CK,u.slice(12));
    const data=JSON.parse(new TextDecoder().decode(pt));const cu=+data['rt-updated']||0,lu=+(localStorage.getItem('rt-updated')||0);
    const before=JSON.stringify(snap());const changed=mergeIn(data,cu>lu);
    if(JSON.stringify(snap())!==JSON.stringify(Object.assign({},data,{'rt-updated':undefined}))||lu>cu)await cloudPush(true);
    if(changed){cmsg('Loaded progress from the cloud.');setTimeout(()=>location.reload(),400);return}
    cmsg('Cloud save is up to date.')}
  catch(e){cmsg('Cloud save is offline. Progress is still saved on this computer.')}}
async function cloudInit(pw){if(!/(^|\\.)justshove\\.com$|\\.vercel\\.app$|^localhost$/.test(location.hostname))return;
  const enc=new TextEncoder();CKEY=[...new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode('epk-save-v1:'+pw)))].map(b=>b.toString(16).padStart(2,'0')).join('');
  const base=await crypto.subtle.importKey('raw',enc.encode(pw),'PBKDF2',false,['deriveKey']);
  CK=await crypto.subtle.deriveKey({name:'PBKDF2',salt:enc.encode('epk-cloud-salt-v1'),iterations:150000,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
  window.__cloudDirty=()=>{cloudDirtyFlag=true;clearTimeout(cloudT);cloudT=setTimeout(()=>cloudPush(false),5000)};
  window.__cloudNow=()=>{if(Date.now()-lastPush>20000){clearTimeout(cloudT);cloudT=setTimeout(()=>cloudPush(true),1500)}};
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden'&&cloudDirtyFlag)cloudPush(true)});
  await cloudPull()}

/* ---------- password lock (photos are encrypted) ---------- */
const ENCP=fetch('faces.bin').then(r=>r.arrayBuffer()).then(a=>{const u=new Uint8Array(a);return{salt:u.slice(0,16),iv:u.slice(16,28),ct:u.slice(28),iter:250000}});
const b64d=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function tryUnlock(pw){
  const ENC=await ENCP;
  const base=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
  const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:ENC.salt,iterations:ENC.iter,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
  const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:ENC.iv},key,ENC.ct);
  setFaces(JSON.parse(new TextDecoder().decode(pt)));react('happy','idle','',0);
  document.getElementById('lock').remove();
  cloudInit(pw).catch(()=>cmsg('Cloud save is offline. Progress is still saved on this computer.'));
}
const lockForm=document.getElementById('lockForm');
lockForm.addEventListener('submit',async e=>{e.preventDefault();const pw=document.getElementById('lockPw').value;
  try{await tryUnlock(pw);store.set('rt-pw',pw)}catch(err){document.getElementById('lockErr').textContent='That password did not work. Try again.'}});
(async()=>{const saved=store.get('rt-pw',null);if(saved){try{await tryUnlock(saved)}catch(e){store.set('rt-pw',null)}}
  const i=document.getElementById('lockPw');if(i)i.focus()})();
"""
open('dist/faces.bin','wb').write(salt+iv+ct)

s = s.replace('.foot{', css + '.foot{', 1)
s = s.replace('<div class="wrap">', html + '<div class="wrap">', 1)
idx = s.rfind('})();')
s = s[:idx] + js + s[idx:]
# game keys must not fire while locked
s = s.replace("document.addEventListener('keydown',e=>{\n", "document.addEventListener('keydown',e=>{\n  if(document.getElementById('lock'))return;\n", 1)

head = '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<meta name="robots" content="noindex, nofollow">\n'
lines = s.split('\n')
out = head + '\n'.join(lines[:3]) + '\n</head><body>\n' + '\n'.join(lines[3:]) + '\n</body></html>\n'

open('dist/index.html', 'w').write(out)
# slim: drop unused Spanish strings, comments, indentation
out=re.sub(r"\n es:\{menu:'Mundos'.*?canvas:'Juego de mecanografía'\},","",out,flags=re.S)
out=re.sub(r"/\* -{5,}[^*]*?\*/","",out)
out='\n'.join(l.strip() for l in out.split('\n') if l.strip())+'\n'
out=out.replace('if(location.search.indexOf(\'debug\')>=0)window.__G=()=>G;\n','')
open('dist/index.html','w').write(out)
assert 'base64,' not in out, 'photo leaked unencrypted'
print('built', len(out))
shutil.copytree('api','dist/api',dirs_exist_ok=True); shutil.copy('package.json','dist/package.json')
print('ready to deploy: dist/')
