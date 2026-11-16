{
  "schema": "orchkit-verdict-v1",
  "utc": "2026-11-16T13:41:34Z",
  "reviewer_lane": "codex_review_orchkit_core_4",
  "requested_head": "4601700f",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "scope_files": [
    "tools/orchkit/anon.py",
    "tools/orchkit/ANON_WORDS.txt",
    "tools/orchkit/launch.py",
    "tools/orchkit/pins.py",
    "tools/orchkit/util.py",
    "tools/orchkit/ledger.py",
    "tools/orchkit/templates/job.sh.tmpl",
    "tools/orchkit/schema",
    "tools/orchkit/examples/read_step.config.json",
    "tools/orchkit/tests"
  ],
  "validation": {
    "method": "Reran the original OC-01 through OC-05, OC-09 and OC-10 reproductions. Adapted OC-06 through OC-08 to the current allocation, exclusive-intent and pinned-byte operations. Exercised actual prepare for OC-02 and OC-10 and all new findings. Filesystem mutations and transport were mocked.",
    "unit_test_output": "Ran 1 test in 0.003s\nOK",
    "full_suite": "Not run: this session prohibits filesystem writes, and some suite fixtures read outside the permitted paths.",
    "fix_3_review": "No verified defect introduced by FIX_3 was found. Its single-place change rejects OC-10. The four new findings below remain in current head but predate FIX_3. Reconstructing the pre-FIX_3 single-place implementation in memory reproduced OC-14 before and after the change.",
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. OC-05 used a local shell function named squeue."
  },
  "reproduction_context": {
    "instructions": "For OC-11 through OC-14, execute python_prelude followed by the finding's repro_python using /usr/bin/python3 -B -c. All virtual paths are served from memory.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools"
    },
    "python_prelude": "import io,os,json,copy,tarfile,zipfile\nfrom contextlib import ExitStack\nfrom unittest.mock import patch\nfrom orchkit import anon,pins,launch,util,ledger\nrules=anon.load_rules()\nexample=util.read_json(launch.HERE+'/examples/read_step.config.json')\nreal_open=open; real_isfile=os.path.isfile\nT='0123456789abcdef'; U='fedcba9876543210'\nclass FD(io.BytesIO):\n def fileno(self):return 99\ndef fixture(extra=None,change=None):\n files={'/v/kit/data.bin':b'ok'}\n for n,b in (extra or {}).items():files['/v/kit/'+n]=b\n manifest={'schema':pins.SCHEMA,'created_utc':'2026-11-16T00:00:00Z','commit':None,'source_seal':None,'entries':[\n {'role':'input','logical_path':os.path.basename(n),'bytes':len(b),'sha256':util.sha256_bytes(b),'source':{'kind':'file','uri':os.path.basename(n),'generation':None}} for n,b in sorted(files.items())]}\n c=copy.deepcopy(example);c['kit_pins_sha256']=pins.kit_identity(manifest)\n if change:change(c)\n files['/v/kit/PINS.json']=util.canonical_json(manifest);files['/v/kit/CONFIG.json']=util.canonical_json(c)\n return files,c\ndef environment(files):\n stack=ExitStack()\n def opening(path,*a,**kw):\n  path=str(path)\n  if path in files:return io.BytesIO(files[path])\n  if path.startswith(launch.HERE+'/'):return real_open(path,*a,**kw)\n  raise AssertionError('unexpected read '+path)\n def isfile(path):return str(path) in files or (str(path).startswith(launch.HERE+'/') and real_isfile(path))\n def walk(path):\n  assert path=='/v/kit',path\n  return [('/v/kit',[],[os.path.basename(n) for n in files if n.startswith('/v/kit/')])]\n def write(path,data):files[path]=data\n for obj,name,value in [(os.path,'isfile',isfile),(os.path,'islink',lambda p:False),(os.path,'lexists',lambda p:False),(os.path,'exists',lambda p:p in files),(os.path,'getsize',lambda p:len(files[p])),(os,'walk',walk),(os,'access',lambda *a:False),(os,'makedirs',lambda *a:None),(util,'atomic_write',write),(ledger,'append',lambda *a,**k:None),(os,'open',lambda *a:99),(os,'fdopen',lambda *a:FD()),(os,'fsync',lambda *a:None)]:\n  stack.enter_context(patch.object(obj,name,value))\n stack.enter_context(patch('builtins.open',opening))\n return stack\ndef prep(files,hook=None):\n def provenance(*a):\n  if hook:hook()\n  return {'repo_commit':'f'*40,'checkout':'/v/epoch','dirty':False,'config_sha256':util.sha256_bytes(files['/v/kit/CONFIG.json'])}\n return launch.prepare('/v/kit','/v/kit/CONFIG.json','/v/prep','review','test','/v/epoch',no_dryrun_reason='fixture',ledger_file='/v/ledger',provenance_fn=provenance,token=T,rules=rules)\ndef payload(files):\n text=files['/v/prep/BATCH.sh'].decode()\n raw=bytes.fromhex(text.split(\"PAYLOAD = '''\\n\",1)[1].split(\"'''\",1)[0].replace('\\n',''))\n with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as a:return {m.name:a.extractfile(m).read() for m in a}\n"
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {
        "status": "fixed",
        "detail": "All five original fixtures produce opacity hits or fail closed."
      },
      "output": [
        "disguised_gzip [{'where': 'a.bin!gz', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.bin!gz!/x', 'scope': 'text', 'rule': 'rule 19'}]",
        "depth_five [{'where': 'a.tgz!gz!/a.tgz!gz!/a.tgz!gz!/a.tgz!gz!/a.tgz', 'scope': 'size', 'rule': 'too-deep'}]",
        "tar_uname [{'where': 'a.tar', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.tar!/x', 'scope': 'name', 'rule': 'rule 19'}]",
        "fifo_bytes [{'where': 'a.tar', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.tar!/x', 'scope': 'size', 'rule': 'special'}]",
        "utf16 [{'where': 'a.txt', 'scope': 'text', 'rule': 'rule 19'}]"
      ]
    },
    {
      "id": "OC-02",
      "text": {
        "status": "fixed",
        "detail": "The original text-only calls still return empty results. Current prepare rejects each forbidden root, environment and pool fixture through its CONFIG.json name scan. Actual pin verification and single-place checks ran."
      },
      "output": [
        "Original reproduction: schema []; config_hits []; batch_hits []; submit_hits []; actual_env_hits 2",
        "OC-02 root opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "OC-02 env opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "OC-02 pool opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]"
      ]
    },
    {
      "id": "OC-03",
      "text": {
        "status": "fixed",
        "detail": "Both original forbidden strings are detected."
      },
      "output": [
        "ORCH_N30 [{'where': 'x', 'scope': 'text', 'rule': 'rule 29'}]",
        "orchkit-pins-v1-private [{'where': 'x', 'scope': 'text', 'rule': 'rule 39'}]"
      ]
    },
    {
      "id": "OC-04",
      "text": {
        "status": "fixed",
        "detail": "mint_job_name rejects the original token containing a trailing newline."
      },
      "output": [
        "LaunchError: token must be 16 lowercase hex: '0123456789abcdef\\n'"
      ]
    },
    {
      "id": "OC-05",
      "text": {
        "status": "fixed",
        "detail": "A failing mocked squeue stops the generated gate before WOULD_SUBMIT."
      },
      "output": [
        "rc=6 stdout=LIVE unknown: squeue failed"
      ]
    },
    {
      "id": "OC-06",
      "text": {
        "status": "fixed",
        "detail": "The generated room check requests the full 100 MiB allocation. A simulated 16 MiB remaining quota causes refusal. Allocation, truncation and other filesystem operations were mocked."
      },
      "output": [
        "SHORT home [Errno 122] Disk quota exceeded",
        "exit 3",
        "OC-06 required=104857600 quota_remaining=16777216 requested=[104857600] accepted=False"
      ]
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "The deterministic interleaving immediately before exclusive intent creation permits only one caller to reach transport."
      },
      "output": [
        "race transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ', 'another submit of 0123456789abcdef holds the intent; never repeat a submit']"
      ]
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Replacing SUBMIT.sh at intent creation leaves the verified bytes sent unchanged. Replacing it immediately after actual _load_prep hashing causes refusal before transport."
      },
      "output": [
        "swap_at_intent transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ']",
        "swap_after_load transport_calls_same_token 0 altered_bytes_sent False approved_bytes_sent False errors ['SUBMIT.sh changed after prepare']"
      ]
    },
    {
      "id": "OC-09",
      "text": {
        "status": "fixed",
        "detail": "The gzip filename and both compressed-stream trailers produce opacity hits. Both trailers also fail decoding checks."
      },
      "output": [
        "gzip_filename [{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}]",
        "bz2_trailer [{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.bin', 'scope': 'size', 'rule': 'undecodable'}]",
        "xz_trailer [{'where': 'a.bin', 'scope': 'text', 'rule': 'rule 19'}, {'where': 'a.bin', 'scope': 'size', 'rule': 'undecodable'}]"
      ]
    },
    {
      "id": "OC-10",
      "text": {
        "status": "fixed",
        "detail": "The original compression-header hash produces a single-place violation. Actual prepare refuses the fixture. The reconstructed pre-FIX_3 check accepts it."
      },
      "output": [
        "after opacity_hits []",
        "after single_place [{'where': 'a.bin', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]",
        "OC-10 before_FIX3 [] after_FIX3 [{'where': 'a.bin', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]",
        "OC-10 prepare REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.bin\"}]"
      ]
    },
    {
      "id": "OC-11",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/launch.py",
      "line_start": 378,
      "line_end": 393,
      "introduced_by_fix_3": false,
      "text": {
        "status": "not fixed",
        "detail": "prepare verifies and scans kit files, then bundle_bytes reopens them after provenance. Replacing a pinned file during that interval bundles unchecked bytes. The subsequent scans inspect the rendered script's hexadecimal payload without decoding it. Replacing data.bin from b'ok' to b'qwen' during the provenance callback passes prepare, preserves the stale pin, and reaches mocked submission. This is a separate prepare-time race from OC-08."
      },
      "repro_python": "files,c=fixture()\nwith environment(files):\n prep(files,lambda:files.update({'/v/kit/data.bin':b'qwen'}))\n files['/v/GO']=('GO '+T).encode();sent=[]\n with patch.object(ledger,'read_rows',return_value=[ledger.make_row('minted',T)]):\n  result=launch.submit('/v/prep','/v/GO',execute=True,ledger_file='/v/ledger',transport=lambda a,b:(sent.append(b) or (0,b'JOBID=4242\\n',b'')),out=io.StringIO())\n print('OC-11 status',result['status'],'transport_calls',len(sent),'shipped_data',repr(payload(files)['kit/data.bin']))\n",
      "output": [
        "race initial_opacity []",
        "race prepare ACCEPTED shipped_data b'qwen' pinned_data_hash_matches False",
        "OC-11 status SUBMITTED transport_calls 1 shipped_data b'qwen'"
      ],
      "expect": "Validate the exact immutable bytes bundled and sent; reject a replacement before transport."
    },
    {
      "id": "OC-12",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 422,
      "line_end": 447,
      "introduced_by_fix_3": false,
      "text": {
        "status": "not fixed",
        "detail": "submit trusts the token in mutable SUBMIT.json without binding it to the job named inside the verified scripts. Changing only token and job_name from token A to another minted token B leaves both script hashes valid. A GO naming only B then submits the unchanged script for A and records the submission under B. The reproduction uses actual prepare, _load_prep, ledger lookup and submit; transport is mocked."
      },
      "repro_python": "files,c=fixture()\nwith environment(files):\n record=prep(files)\n record['token']=U;record['job_name']=launch.PREFIX+U\n files['/v/prep/SUBMIT.json']=util.canonical_json(record);files['/v/GO']=('GO '+U).encode()\n minted=[ledger.make_row('minted',t) for t in (T,U)];sent=[]\n with patch.object(ledger,'read_rows',return_value=minted):\n  result=launch.submit('/v/prep','/v/GO',execute=True,ledger_file='/v/ledger',transport=lambda a,b:(sent.append(b) or (0,b'JOBID=4242\\n',b'')),out=io.StringIO())\n print('token_swap','go_names_actual_token',launch._names(files['/v/GO'].decode(),T),'sent_original_job',('#SBATCH --job-name='+launch.PREFIX+T).encode() in sent[0],'status',result['status'],'reported_token',result['token'])\n",
      "output": [
        "token_swap go_names_actual_token False sent_original_job True status SUBMITTED reported_token fedcba9876543210"
      ],
      "expect": "Bind the GO token and ledger identity to the actual submitted job and payload; refuse inconsistent preparation metadata."
    },
    {
      "id": "OC-13",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 97,
      "line_end": 101,
      "introduced_by_fix_3": false,
      "text": {
        "status": "not fixed",
        "detail": "ZIP recognition requires its signature at byte zero. Python's ZIP reader accepts an archive with a prepended script, but the scanner treats that archive as ordinary bytes and misses compressed forbidden content. A deflated ZIP containing qwen is rejected normally; prepending a shebang makes the scan and actual prepare accept it. The bundle preserves the readable ZIP unchanged."
      },
      "repro_python": "z=io.BytesIO()\nwith zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as a:a.writestr('x',b'qwen')\nfor prefix in [b'',b'#!/usr/bin/env python3\\n']:\n data=prefix+z.getvalue();files,c=fixture({'a.zip':data})\n with environment(files):\n  print('prefix_zip',bool(prefix),'hits',anon.scan_tree('/v/kit',rules))\n  try:\n   prep(files);print('prefix_zip prepare ACCEPTED decoded',zipfile.ZipFile(io.BytesIO(payload(files)['kit/a.zip'])).read('x'))\n  except launch.LaunchError as e:print('prefix_zip prepare REFUSED',str(e)[:130])\n",
      "output": [
        "prefix_zip False hits [{'where': 'a.zip!/x', 'scope': 'text', 'rule': 'rule 19'}]",
        "prefix_zip prepare REFUSED opacity: [{\"rule\": \"rule 19\", \"scope\": \"text\", \"where\": \"a.zip!/x\"}]",
        "prefix_zip True hits []",
        "prefix_zip prepare ACCEPTED decoded b'qwen'"
      ],
      "expect": "Recognize and inspect prefixed ZIP archives, or reject them before bundling."
    },
    {
      "id": "OC-14",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/pins.py",
      "line_start": 205,
      "line_end": 232,
      "introduced_by_fix_3": false,
      "text": {
        "status": "not fixed",
        "detail": "The single-place check still skips shipped hash copies in three verified representations. Parsing JSON discards earlier duplicate-key values, and _json_hex_parent ignores a top-level string. The non-JSON fallback scans Latin-1 only, missing UTF-16 hashes. Each fixture contains data.bin's current SHA-256 outside PINS.json, passes actual prepare, and is bundled unchanged. All three also pass the reconstructed pre-FIX_3 implementation."
      },
      "repro_python": "digest=util.sha256_bytes(b'ok')\nfor label,blob in [('duplicate_key',b'{\"x\":\"'+digest.encode()+b'\",\"x\":\"ok\"}'),('root_string',json.dumps(digest).encode()),('utf16',digest.encode('utf-16'))]:\n name='a.txt' if label=='utf16' else 'a.json'\n files,c=fixture({name:blob})\n with environment(files):\n  print('single_place',label,pins.check_single_place('/v/kit'))\n  try:prep(files);print('single_place',label,'prepare ACCEPTED preserved',payload(files)['kit/'+name]==blob)\n  except launch.LaunchError as e:print('single_place',label,'REFUSED',e)\n",
      "output": [
        "single_place duplicate_key []",
        "single_place duplicate_key prepare ACCEPTED preserved True",
        "single_place root_string []",
        "single_place root_string prepare ACCEPTED preserved True",
        "single_place utf16 []",
        "single_place utf16 prepare ACCEPTED preserved True"
      ],
      "baseline_output": [
        "duplicate_key before_FIX3 [] after_FIX3 []",
        "root_string before_FIX3 [] after_FIX3 []",
        "utf16 before_FIX3 [] after_FIX3 []"
      ],
      "expect": "Inspect all shipped hash occurrences, including discarded JSON values, root strings and UTF-16 text, while preserving explicit field exceptions."
    }
  ]
}

OC-01 through OC-10 pass their targeted reproductions.
Four remaining bypasses keep the verdict at NO_GO.
No new regression attributable to FIX_3 was verified.
One unit test passed; the full suite was not run.
No files changed or external commands ran.