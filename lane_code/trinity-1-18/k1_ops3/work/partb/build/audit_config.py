"""Validate every sealed configuration field, including retained native assets."""
import base64
from pathlib import PurePosixPath
import re

def audit(config):
    checked = {}
    def check(ok, path, rule):
        if not ok:
            raise ValueError(path + ': ' + rule)
        checked[path] = rule
    def sha(value, path):
        check(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), path, 'SHA256 hex')
    def path(value, key, absolute=True):
        check(isinstance(value, str) and bool(value) and not any(c.isspace() for c in value)
              and '..' not in PurePosixPath(value).parts and '<' not in value and '>' not in value
              and PurePosixPath(value).is_absolute() == absolute, key, 'canonical path')
    def walk(value, key):
        if isinstance(value, dict):
            check(bool(value), key, 'nonempty object')
            for k,v in value.items():
                child = key + '.' + k
                if k in ('members', 'tree_sources', 'frames_inventory'):
                    check(isinstance(v,dict) and bool(v), child, 'path-indexed inventory')
                    for name,row in v.items():
                        path(name, child+'.<path>', False)
                        if k == 'members':
                            check(isinstance(row,dict) and set(row)=={'bytes','sha256'}, child+'.*', 'bytes/SHA256 record')
                            check(type(row['bytes']) is int and row['bytes']>=0, child+'.*.bytes', 'nonnegative integer')
                            sha(row['sha256'], child+'.*.sha256')
                        else:
                            sha(row, child+'.*')
                    checked[child] += '; '+str(len(v))+' entries checked'
                elif k in ('sha256','manifest_sha256','manifest_binding_digest'):
                    sha(v,child)
                elif k == 'generation':
                    check(isinstance(v,str) and v.isdigit() and int(v)>0,child,'positive pinned generation')
                elif k in ('bytes','expanded_bytes','allocation_seconds','capture_reserve_seconds','return_margin_seconds','canary_limit_seconds'):
                    check(type(v) is int and v>=0,child,'nonnegative integer')
                elif k == 'deadline_unix':
                    check(type(v) is int and v>0,child,'optional positive epoch')
                elif k in ('md5','crc32c'):
                    check(isinstance(v,str) and len(base64.b64decode(v,validate=True)) == (16 if k=='md5' else 4),child,'base64 checksum')
                elif k in ('path','logical_path','logical_root','destination','export_destination','manifest','tower_binding','logical_run','pool','pointer','trainer_logical_archive','tree_root','aliases_root','kit_import_root','frames_source','gcloud_config') and isinstance(v,str):
                    path(v,child)
                elif k in ('name','cloud_prefix'):
                    path(v,child,False)
                elif k == 'frame_request':
                    check(isinstance(v,str) and all(re.fullmatch('[0-9a-f]{64}',s) for s in v.splitlines()),child,'newline-separated frame hashes')
                elif k == 'cloud':
                    check(isinstance(v,str) and v.startswith('gs://cmu-gpucloud-jjyeung/q8/'),child,'return bucket URI')
                elif k == 'captures_unchanged':
                    check(v is True,child,'production capture identity')
                elif k == 'token':
                    check(isinstance(v,str) and re.fullmatch('[0-9a-f]+',v),child,'opaque hex token')
                elif k in ('schema','role'):
                    check(isinstance(v,str) and re.fullmatch('[A-Za-z0-9_-]+',v),child,'schema or role identifier')
                else:
                    walk(v,child)
        elif isinstance(value,list):
            check(bool(value),key,'nonempty list')
            for i,v in enumerate(value): walk(v,key+'['+str(i)+']')
        else:
            raise ValueError('Unaudited field: '+key+' ('+type(value).__name__+')')
    walk(config,'config')
    check(config['export']['bytes']==sum(p['bytes'] for p in config['export']['parts']), 'config.export.total', 'sum of ordered part sizes')
    check(config['pointer']==config['pool']+'/a.json','config.pointer_relation','stable pool pointer')
    check(config['anchors']['logical_root']=='/scratch/jjyeung/k1_frames','config.anchors.destination_relation','stage a1 destination, strip=0')
    return dict(passed=True, fields=checked,
                inactive_native_fields=['assets.depth','assets.frame_puller','assets.frame_request','assets.frames_inventory',
                    'assets.frames_source','assets.schema','assets.vnice','assets.small_objects[0]',
                    'assets.small_objects[2]','assets.small_objects[4]'],
                runtime_fields={'started_unix':'finite allocation start from time.time()',
                    'source':'logical_run assigned after staging', 'pool':'pool plus numeric SLURM_JOB_ID',
                    'metadata_mapping':'absent in production; CPU-only exact-file transport'})
