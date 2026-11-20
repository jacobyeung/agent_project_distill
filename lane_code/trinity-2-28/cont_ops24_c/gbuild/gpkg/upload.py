def upload_capture(root, cfg, out, return_token, R):
    """Best-effort large-object publication; normal return always follows."""
    from orchard_h10.common import write, sha, opaque
    path = Path(root)/'sj'/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'c/0.gz'
    result = dict(uri=R.GCS_ROOT+'/'+return_token+'c/0.gz', generation=None,
                  bytes=0, sha256=None, items=0, verified=False, error=None)
    try:
        if Path(out).resolve() in path.resolve().parents or str(path).startswith('/project/'):
            raise ValueError('invalid local capture path')
        progress = Path(out)/'metadata/4.json'
        if progress.exists(): result['items'] = json.loads(progress.read_text())['items']
        if not path.is_file(): raise ValueError('capture absent')
        result.update(bytes=path.stat().st_size, sha256=sha(path))
        if result['bytes'] > 1_900_000_000: raise ValueError('capture cap exceeded')
        # Use the same service configuration as the normal return, with no inherited secrets.
        env = {k:v for k,v in os.environ.items() if k in ('PATH','HOME','USER','TMPDIR')}
        env['CLOUDSDK_CONFIG'] = R.CLOUD_CONFIG
        opaque([str(path), result['uri'], *[k+'='+v for k,v in env.items()]])
        subprocess.run(['gcloud','storage','cp',str(path),result['uri']], env=env,
                       check=True, capture_output=True, timeout=1800)
        desc = subprocess.run(['gcloud','storage','objects','describe',result['uri'],'--format=json'],
                              env=env, check=True, capture_output=True, text=True, timeout=60)
        meta = json.loads(desc.stdout); generation = str(meta.get('generation',''))
        if not generation.isdigit() or int(meta.get('size',-1)) != result['bytes']:
            raise ValueError('object metadata differs')
        result['generation'] = generation
        check = path.parent/'1.gz'
        with check.open('xb') as stream:
            subprocess.run(['gcloud','storage','cat',result['uri']+'#'+generation], env=env,
                           check=True, stdout=stream, stderr=subprocess.PIPE, timeout=1800)
        if check.stat().st_size != result['bytes'] or sha(check) != result['sha256']:
            raise ValueError('object readback differs')
        result['verified'] = True
    except Exception as error:
        result['error'] = type(error).__name__+': '+str(error)
    write(Path(out)/'metadata/CAPTURE.json', result)
    return result
