{
  "schema": "orchkit-verdict-v1",
  "utc": "2026-11-16T13:13:40Z",
  "reviewer_lane": "codex_review_orchkit_core",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "scope_files": [
    "tools/orchkit/anon.py",
    "tools/orchkit/ANON_WORDS.txt",
    "tools/orchkit/launch.py",
    "tools/orchkit/templates/job.sh.tmpl",
    "tools/orchkit/schema/config.schema.json",
    "tools/orchkit/pack.py",
    "tools/orchkit/pins.py",
    "tools/orchkit/ledger.py",
    "tools/orchkit/util.py",
    "tools/orchkit/stage.py",
    "tools/orchkit/ret.py",
    "tools/orchkit/tests/test_anon.py",
    "tools/orchkit/tests/test_launch.py",
    "tools/orchkit/examples/read_step.config.json",
    "/scratch/jjyeung/orch_n30/e_orchkit-core/REPORT.md"
  ],
  "repro_suite": [
    [
      "env",
      "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONDONTWRITEBYTECODE=1",
      "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
      "/usr/bin/python3",
      "-B",
      "-c",
      "import sys,unittest,datetime; sys.path.insert(0,'/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools/orchkit/tests'); from test_launch import JobNameTest; result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(JobNameTest)); print('utc='+datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')); sys.exit(not result.wasSuccessful())"
    ]
  ],
  "findings": [
    {
      "id": "OC-01",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 77,
      "line_end": 175,
      "text": "The scanner accepts forbidden content through five verified paths: a gzip tar named a.bin, five nested compressed tars, a tar header's uname, bytes attached to a FIFO member, and UTF-16 text. Each fixture contains qwen, but all five scans returned []. Compression detection depends on names or uncompressed magic; recursion stops at depth four; archive bytes and nonregular-member bodies are skipped; text is decoded only as Latin-1. These files can be bundled unchanged after passing opacity checks.",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import io,tarfile,gzip\nfrom unittest.mock import patch\nfrom orchkit import anon\nr=anon.load_rules()\ndef tar(name,data,uname='',kind=tarfile.REGTYPE):\n b=io.BytesIO()\n with tarfile.open(fileobj=b,mode='w') as a:\n  t=tarfile.TarInfo(name);t.size=len(data);t.uname=uname;t.type=kind;a.addfile(t,io.BytesIO(data))\n return b.getvalue()\ndef scan(name,data):\n with patch('os.path.isfile',return_value=True),patch('os.path.islink',return_value=False),patch('os.path.getsize',return_value=len(data)),patch('builtins.open',side_effect=lambda *a,**k:io.BytesIO(data)):\n  return anon.scan_tree(name,r)\nb=gzip.compress(tar('x',b'qwen'))\nprint('disguised_gzip',scan('a.bin',b))\nfor _ in range(4): b=gzip.compress(tar('a.tgz',b))\nprint('depth_five',scan('a.tgz',b))\nprint('tar_uname',scan('a.tar',tar('x',b'ok',uname='qwen')))\nprint('fifo_bytes',scan('a.tar',tar('x',b'qwen',kind=tarfile.FIFOTYPE)))\nprint('utf16',scan('a.txt','qwen'.encode('utf-16')))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-02",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/launch.py",
      "line_start": 372,
      "line_end": 386,
      "text": "prepare passes env={} and checks CONFIG.json and SUBMIT.sh only as text. Consequently the name-only split rule misses configured environment names, environment values, root_parent, and pool/log paths. A schema-valid configuration containing /tmp/split, /project/u/split/logs, and SPLIT_MODEL passed every corresponding preparation scan. Output: schema []; config_hits []; batch_hits []; submit_hits []; actual_env_hits 2.",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "from orchkit import anon,launch,util\nc=util.read_json(launch.HERE+'/examples/read_step.config.json');r=anon.load_rules()\nc['job']['root_parent']='/tmp/split';c['return']['pool']='/project/u/split/logs';c['return']['gcs_env']={'SPLIT_MODEL':'/project/u/split/a'}\ns=launch.render(c,'0123456789abcdef',b'x');remote=launch.submit_script(c,'0123456789abcdef',s)\nprint('schema',launch.validate_config(c))\nprint('config_hits',anon.scan_bytes('CONFIG.json',util.canonical_json(c),r))\nprint('batch_hits',anon.scan_job(r,script=s,argv=c['entry'],env={}))\nprint('submit_hits',anon.scan_text('SUBMIT.sh',remote,r,'text'))\nprint('actual_env_hits',len(anon.scan_job(r,env=c['return']['gcs_env'])))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-03",
      "severity": "fix",
      "class": "legality",
      "file": "tools/orchkit/ANON_WORDS.txt",
      "line_start": 29,
      "line_end": 40,
      "text": "The lane regex is case-sensitive, and the library exception accepts an allowed identifier as the prefix of a longer forbidden name. File contents naming ORCH_N30 or orchkit-pins-v1-private therefore pass. Output: ORCH_N30 []; orchkit-pins-v1-private [].",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "from orchkit import anon\nr=anon.load_rules()\nfor x in ['ORCH_N30','orchkit-pins-v1-private']:\n print(x,anon.scan_text('x',x,r,'text'))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-04",
      "severity": "fix",
      "class": "plumbing",
      "file": "tools/orchkit/launch.py",
      "line_start": 63,
      "line_end": 72,
      "text": "mint_job_name accepts a supplied token with a trailing newline because Python's $ anchor permits a match before the final newline. It returns a name longer than the required prefix plus 16 hex characters, and scan_job also accepts it. Output: 'a15_cot_ap0123456789abcdef\\n' exact=False hits=[].",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import re\nfrom orchkit import anon,launch\nt,n=launch.mint_job_name('0123456789abcdef\\n')\nprint(repr(n),'exact='+str(re.fullmatch('a15_cot_ap[0-9a-f]{16}',n) is not None),'hits='+str(anon.scan_job(anon.load_rules(),job_name=n)))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-05",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 255,
      "line_end": 264,
      "text": "The remote live-job gate fails open when squeue fails. Its pipeline ends in || true, so an unavailable scheduler query becomes an empty job list and execution continues toward sbatch. The local ledger cannot cover jobs absent from that ledger. Running the generated gate with a local squeue shell function returning 1 produced rc=0 stdout=WOULD_SUBMIT.",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import subprocess\nfrom orchkit import launch\ns='set -euo pipefail\\nsqueue(){ return 1; }\\n'+launch.live_check('general')+'\\necho WOULD_SUBMIT\\n'\np=subprocess.run(['bash','-s'],input=s.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)\nprint('rc=%d stdout=%s'%(p.returncode,p.stdout.decode().strip()))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-06",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 278,
      "line_end": 295,
      "text": "The room check compares the budget with filesystem free space and probes only min(budget, 8 MiB); it does not establish that the user's remaining quota covers the budget. Executing the generated Python check against a simulated filesystem with 1 GiB free and 16 MiB of remaining quota accepted a 100 MiB home budget. Output: ROOM home free=1073741824 need=104857600; required=104857600 quota_remaining=16777216 probed=8388608 accepted=True. The same room function checks the pool.",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import io,types\nfrom unittest.mock import patch, mock_open\nfrom orchkit import launch\nneed=100<<20; remaining=16<<20; writes=[]\ns=launch.submit_script({'job':{'partition':'general'},'budgets':{'home':{'max_bytes':need}}},'0123456789abcdef','#!/bin/bash\\n')\ncheck=s.split(\"CHECK_0123456789abcdef'\\n\",1)[1].split('\\nCHECK_0123456789abcdef',1)[0]\ndef write(b):\n writes.append(len(b))\n if len(b)>remaining: raise OSError(122,'Disk quota exceeded')\n return len(b)\nm=mock_open();m.return_value.write.side_effect=write\nwith patch('os.statvfs',return_value=types.SimpleNamespace(f_bavail=1<<30,f_frsize=1)),patch('builtins.open',m),patch('os.fsync'):\n exec(check)\nprint('required=%d quota_remaining=%d probed=%d accepted=True'%(need,remaining,max(writes)))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-07",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 438,
      "line_end": 462,
      "text": "The repeat-submission check and intent write are not atomic. Two callers can both observe no submitted row and no intent, then both reach transport. atomic_write replaces an existing destination rather than exclusively claiming the token. A deterministic in-memory interleaving entered the second submit immediately before the first intent write; both reached mocked transport. Output: transport_calls_same_token 2. No real submission occurred.",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import io\nfrom unittest.mock import patch,mock_open\nfrom orchkit import launch\nt='0123456789abcdef';state={'intent':False,'nested':False};calls=[]\nr=dict(token=t,partition='general',argv=['fake'],stdin='SUBMIT.sh')\ndef transport(a,b): calls.append(b);return 1,b'',b''\ndef run():\n try: launch.submit('/virtual','/virtual/GO',execute=True,transport=transport,out=io.StringIO())\n except launch.LaunchError: pass\ndef write(path,obj):\n if path.endswith('SUBMIT_INTENT.json'):\n  if not state['nested']: state['nested']=True;run()\n  state['intent']=True\nwith patch.object(launch,'_load_prep',return_value=r),patch('os.path.isfile',return_value=True),patch('os.path.exists',side_effect=lambda p:state['intent']),patch('builtins.open',mock_open(read_data=t.encode())),patch.object(launch.ledger,'lookup',return_value=[{'event':'minted'}]),patch.object(launch.ledger,'live',return_value=[]),patch.object(launch.util,'write_json',side_effect=write):\n run()\nprint('transport_calls_same_token',len(calls))\n"
      ],
      "expect": "fail_before_pass_after"
    },
    {
      "id": "OC-08",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 430,
      "line_end": 462,
      "text": "submit verifies SUBMIT.sh in _load_prep, then reopens it after the GO, ledger, and intent operations without verifying the bytes it sends. Replacing SUBMIT.sh during that interval sends unchecked commands instead of the prepared submission script, bypassing its batch digest, opacity, room, and live-job checks. The reproduction used actual _load_prep hashing over in-memory files, replaced SUBMIT.sh at the intent write, and captured the replacement in mocked transport. Output: altered_bytes_sent True.",
      "repro": [
        "env",
        "TMPDIR=/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
        "PYTHONPATH=/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
        "/usr/bin/python3",
        "-B",
        "-c",
        "import io,json,os\nfrom unittest.mock import patch\nfrom orchkit import launch,util\nt='0123456789abcdef';p='/virtual';good=b'#!/bin/bash\\necho approved\\n';bad=b'#!/bin/bash\\necho qwen\\n'\nr=dict(token=t,partition='general',argv=['fake'],stdin='SUBMIT.sh',script_sha256=util.sha256_bytes(good),submit_sha256=util.sha256_bytes(good))\nfiles={'SUBMIT.json':json.dumps(r).encode(),'BATCH.sh':good,'SUBMIT.sh':good,'GO':t.encode()}\nsent=[]\ndef opening(path,*a,**k): return io.BytesIO(files[os.path.basename(path)])\ndef write(path,obj):\n if path.endswith('SUBMIT_INTENT.json'): files['SUBMIT.sh']=bad\nwith patch('builtins.open',opening),patch('os.path.isfile',return_value=True),patch('os.path.exists',return_value=False),patch.object(launch.ledger,'lookup',return_value=[{'event':'minted'}]),patch.object(launch.ledger,'live',return_value=[]),patch.object(util,'write_json',side_effect=write):\n try: launch.submit(p,p+'/GO',execute=True,out=io.StringIO(),transport=lambda a,b:(sent.append(b) or (1,b'',b'')))\n except launch.LaunchError: pass\nprint('altered_bytes_sent',len(sent)==1 and bad in sent[0])\n"
      ],
      "expect": "fail_before_pass_after"
    }
  ]
}
Eight findings require correction before approval.
The existing job-name test passed; the full suite was not run under the read-only filesystem restriction.
All defect reproductions ran locally with in-memory fixtures or mocked transport. No files were changed, and no network or scheduler commands ran.