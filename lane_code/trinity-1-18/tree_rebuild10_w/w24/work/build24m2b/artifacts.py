def publish_artifacts(target, root):
    base=root/'dr/p/q/selection'
    if not base.is_dir():base=root/'p/q/selection'
    paths=[base/name for name in ('receipt.json','materialization.json')]
    if not all(p.is_file() and not p.is_symlink() for p in paths):return
    if sum(p.stat().st_size for p in paths)>5_000_000:
        raise ValueError('R1_ROUTING_ARTIFACTS_TOO_LARGE')
    for p in paths:
        raw=p.read_bytes();json.loads(raw)
        fd=os.open(target/(p.name+'.part'),os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw)
        os.replace(target/(p.name+'.part'),target/p.name)
        print(p.name+' sha256='+hashlib.sha256(raw).hexdigest(),flush=True)
