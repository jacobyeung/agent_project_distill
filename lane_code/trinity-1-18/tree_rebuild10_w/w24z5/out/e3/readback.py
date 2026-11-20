"""Run on the credentialed node; keep credentials in memory and read serially."""
import argparse,base64,hashlib,json,subprocess,sys,urllib.parse

def main():
 p=argparse.ArgumentParser();p.add_argument('report');p.add_argument('--bucket',required=True);a=p.parse_args()
 report=json.load(open(a.report));rows=report['objects']
 archive=report['archive'];parts={}
 if report.get('status')!='PASS' or report['checks'].get('archive_while_full')!='PASS':raise ValueError('E34')
 token=subprocess.run(['gcloud','auth','print-access-token'],capture_output=True,text=True,check=True).stdout.strip()
 if not token or '\n' in token or '"' in token:raise ValueError('E31')
 config='header = "Authorization: Bearer '+token+'"\n'
 def get(url):
  r=subprocess.run(['curl','--silent','--show-error','--fail','--limit-rate','8M','--config','-',url],input=config.encode(),capture_output=True)
  if r.returncode:raise ValueError('E32')
  return r.stdout
 passed=True
 for row in rows:
  name=urllib.parse.quote(row['name'],safe='');bucket=urllib.parse.quote(a.bucket,safe='')
  generation=row['response'].get('generation')
  if not generation:raise ValueError('E33')
  query='generation='+urllib.parse.quote(str(generation),safe='')
  base='https://storage.googleapis.com/storage/v1/b/'+bucket+'/o/'+name
  meta=json.loads(get(base+'?'+query));raw=get(base+'?alt=media&'+query)
  sha=hashlib.sha256(raw).hexdigest();md5=base64.b64encode(hashlib.md5(raw).digest()).decode()
  good=(meta['name']==row['name'] and int(meta['size'])==row['bytes']==len(raw)
        and sha==row['sha256'] and md5==meta.get('md5Hash')==row['response'].get('md5Hash')
        and meta.get('crc32c')==row['response'].get('crc32c'))
  if row['name'] in archive['objects']:parts[row['name']]=raw
  passed=passed and good
  print(json.dumps(dict(name=row['name'],bytes=len(raw),sha256=sha,status='PASS' if good else 'FAIL')),flush=True)
 raw=b''.join(parts.get(name,b'') for name in archive['objects'])
 good=(len(parts)==4 and len(raw)==archive['bytes'] and hashlib.sha256(raw).hexdigest()==archive['sha256'])
 print(json.dumps(dict(archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),status='PASS' if good else 'FAIL')))
 return 0 if passed and good and len(rows)==20 else 1

if __name__=='__main__':
 try:raise SystemExit(main())
 except Exception as e:print('E3_READ_FAIL '+type(e).__name__,file=sys.stderr);raise SystemExit(1)
