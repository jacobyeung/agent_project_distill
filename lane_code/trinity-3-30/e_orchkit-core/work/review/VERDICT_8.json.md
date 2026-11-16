{
  "schema": "orchkit-verdict-v1",
  "reviewer_lane": "codex_review_orchkit_core_8",
  "requested_head": "5b3301f2",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "validation": {
    "method": "Reran OC-01..OC-21 with filesystem mocks adapted to the current snapshot, exclusive-claim and partition-lock operations. Preparation, scanning, pin verification, rebuilding and submission ran against in-memory fixtures. Transport was mocked. flock was modeled by lock-file path.",
    "unit_test_output": "Ran 1 test in 0.003s\nOK",
    "full_suite": "Not run because its fixtures require filesystem writes unavailable in this read-only session.",
    "go_controls": [
      "NO_GO 0123456789abcdef: REFUSED, transport_calls 0",
      "GO fedcba9876543210: REFUSED, transport_calls 0",
      "GO: a15_cot_ap0123456789abcdef: SUBMITTED, mocked transport_calls 1"
    ],
    "partition_lock_control": "Without metadata changes, concurrent submissions to general produce one mocked transport call; the second submission is refused.",
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. Remote live-check controls used a local shell function named squeue."
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {
        "status": "fixed",
        "detail": "All five original fixtures are detected or refused."
      },
      "output": "disguised_gzip: rule 19; depth_five: too-deep; tar_uname: rule 19; fifo_bytes: rule 19 and special; utf16: rule 19"
    },
    {
      "id": "OC-02",
      "text": {
        "status": "fixed",
        "detail": "Preparation refuses each original root, environment and pool fixture."
      },
      "output": "root REFUSED; env REFUSED; pool REFUSED; all report CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-03",
      "text": {
        "status": "fixed",
        "detail": "Both original naming bypasses are detected."
      },
      "output": "ORCH_N30: rule 29; orchkit-pins-v1-private: rule 39"
    },
    {
      "id": "OC-04",
      "text": {
        "status": "fixed",
        "detail": "A token with a trailing newline is refused."
      },
      "output": "LaunchError token must be 16 lowercase hex: '0123456789abcdef\\n'"
    },
    {
      "id": "OC-05",
      "text": {
        "status": "fixed",
        "detail": "A failed scheduler query fails closed."
      },
      "output": "rc=6 stdout=LIVE unknown: squeue failed"
    },
    {
      "id": "OC-06",
      "text": {
        "status": "fixed",
        "detail": "The room check attempts allocation of the full budget and refuses the simulated quota shortage."
      },
      "output": "SHORT home [Errno 122] Disk quota exceeded; exit 3; allocated [104857600]"
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "Concurrent attempts using the same preparation reach transport once."
      },
      "output": "second REFUSED already submitted or attempted; transport_calls_same_token 1; submitted_rows 1"
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Replacing SUBMIT.sh at the intent operation does not replace the rebuilt bytes sent."
      },
      "output": "SUBMITTED calls 1; altered_bytes_sent False"
    },
    {
      "id": "OC-09",
      "text": {
        "status": "fixed",
        "detail": "The gzip filename and bz2/xz trailers are detected."
      },
      "output": "gzip_filename: rule 19; bz2_trailer and xz_trailer: rule 19 and undecodable"
    },
    {
      "id": "OC-10",
      "text": {
        "status": "fixed",
        "detail": "The original duplicate hash in a compression header violates the single-place check."
      },
      "output": "a.bin: copy of a pinned hash outside PINS.json"
    },
    {
      "id": "OC-11",
      "text": {
        "status": "fixed",
        "detail": "Changing the source kit during provenance leaves the checked snapshot unchanged."
      },
      "output": "SUBMITTED calls 1; shipped_data b'ok'"
    },
    {
      "id": "OC-12",
      "text": {
        "status": "fixed",
        "detail": "The original token-only metadata substitution is refused."
      },
      "output": "REFUSED the prepared scripts do not belong to token fedcba9876543210; calls 0"
    },
    {
      "id": "OC-13",
      "text": {
        "status": "fixed",
        "detail": "Both ordinary and prefixed valid ZIP archives are inspected."
      },
      "output": "Both fixtures: a.zip!/x rule 19; prepare REFUSED opacity"
    },
    {
      "id": "OC-14",
      "text": {
        "status": "fixed",
        "detail": "Duplicate-key values, root strings and UTF-16 copies of pinned hashes are detected."
      },
      "output": "duplicate_key, root_string, utf16: prepare REFUSED single-place invariant"
    },
    {
      "id": "OC-15",
      "text": {
        "status": "fixed",
        "detail": "Appending an empty ZIP no longer hides the tar interpretation."
      },
      "output": "opacity fixture: a.bin!/x.gz!gz rule 19; hash fixture: single-place violation; both preparations REFUSED"
    },
    {
      "id": "OC-16",
      "text": {
        "status": "fixed",
        "detail": "Both original command substitutions are refused."
      },
      "output": "script: REFUSED SUBMIT.sh differs from its rebuild; argv: REFUSED the transport command differs; transport_calls 0"
    },
    {
      "id": "OC-17",
      "text": {
        "status": "fixed",
        "detail": "The forbidden path in a discarded duplicate CONFIG.json value is detected."
      },
      "output": "CONFIG.json rule 7; prepare REFUSED opacity"
    },
    {
      "id": "OC-18",
      "text": {
        "status": "fixed",
        "detail": "All four original Unicode-escape fixtures are detected."
      },
      "output": "utf16, utf32, gzip_json, json_without_extension: rule 19; prepare REFUSED opacity"
    },
    {
      "id": "OC-19",
      "text": {
        "status": "fixed",
        "detail": "The original damaged ZIP with its signature at byte zero is refused."
      },
      "output": "a.zip: unsupported-container; prepare REFUSED unscannable"
    },
    {
      "id": "OC-20",
      "text": {
        "status": "fixed",
        "detail": "Changing PREP/kit/data.bin at the JOB.json read is caught by validation of the submission snapshot."
      },
      "output": "REFUSED pins differ: actual bytes 4, expected bytes 2; calls 0"
    },
    {
      "id": "OC-21",
      "text": {
        "status": "fixed",
        "detail": "Two preparation copies cannot submit the same token twice. A separate control using different partition-lock names also reaches and is refused by the shared token claim."
      },
      "output": "transport_calls_same_token 1; submitted_rows 1; independent-lock control REFUSED token 0123456789abcdef was already claimed for submission"
    },
    {
      "id": "OC-22",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 511,
      "line_end": 598,
      "text": {
        "status": "not fixed",
        "detail": "The live gate and partition lock trust record['partition'] from mutable SUBMIT.json. Rebuild validates the actual config but never compares its partition with that field. Changing one general preparation's metadata to advanced lets two actual general submissions hold different locks and enter transport concurrently. Both remote live checks can observe an empty queue before either sbatch occurs. The submitted ledger row also records the false partition."
      },
      "repro_python": "for mutate in (False,True):\n files,c=fixture();rows=[];sent=[];outcomes=[]\n with environment(files),patch.object(ledger,'append',side_effect=lambda row,*a:rows.append(row)):\n  first=prep(files)\n  launch.prepare('/v/kit','/v/kit/CONFIG.json','/v/prep2','review','test','/v/epoch',no_dryrun_reason='fixture',ledger_file='/v/ledger',provenance_fn=lambda *a:{},token=U,rules=rules)\n  if mutate:\n   first['partition']='advanced';files['/v/prep/SUBMIT.json']=util.canonical_json(first)\n  files['/v/G1']=('GO '+T).encode();files['/v/G2']=('GO '+U).encode()\n  def transport(a,b):\n   sent.append(b)\n   if len(sent)==1:\n    try:outcomes.append(launch.submit('/v/prep2','/v/G2',execute=True,ledger_file='/v/ledger',transport=transport,out=io.StringIO())['status'])\n    except launch.LaunchError:outcomes.append('REFUSED')\n   return 0,b'JOBID=4242\\n',b''\n  with patch.object(ledger,'read_rows',side_effect=lambda *a:rows[:]):\n   outcomes.append(launch.submit('/v/prep','/v/G1',execute=True,ledger_file='/v/ledger',transport=transport,out=io.StringIO())['status'])\n  print('mutated',mutate,'calls',len(sent),'outcomes',outcomes,'general_scripts',sum(b'#SBATCH --partition=general' in b for b in sent))",
      "output": [
        "mutated False calls 1 outcomes ['REFUSED', 'SUBMITTED'] general_scripts 1",
        "mutated True calls 2 outcomes ['SUBMITTED', 'SUBMITTED'] general_scripts 2"
      ],
      "expect": "Use the ledger-anchored config partition for locking, admission and submitted ledger rows, or refuse inconsistent metadata before admission."
    },
    {
      "id": "OC-23",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 81,
      "line_end": 112,
      "text": {
        "status": "not fixed",
        "detail": "Escape inspection handles only hexadecimal Unicode and byte escapes. Standard Python octal and named-character escapes hide qwen, and standard JSON escaped slashes hide /data2/secret. All three fixtures pass preparation and ship unchanged."
      },
      "repro_python": "for name,blob in [('octal.py',b'x=\"q\\\\167en\"'),('named.py',b'x=\"q\\\\N{LATIN SMALL LETTER W}en\"'),('a.json',b'{\"p\":\"\\\\/data2\\\\/secret\"}')]:\n print('decoded',json.loads(blob) if name.endswith('.json') else ast.literal_eval(blob.decode().split('=',1)[1]))\n accepted(name,blob)",
      "output": [
        "decoded qwen",
        "octal.py hits [] prepare ACCEPTED unchanged True",
        "decoded qwen",
        "named.py hits [] prepare ACCEPTED unchanged True",
        "decoded {'p': '/data2/secret'}",
        "a.json hits [] prepare ACCEPTED unchanged True"
      ],
      "expect": "Inspect these standard escape forms or refuse them."
    },
    {
      "id": "OC-24",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 133,
      "line_end": 157,
      "text": {
        "status": "not fixed",
        "detail": "Malformed-container recognition still fails open. A prefixed ZIP without its end record and a tar with a V7-style header and invalid checksum are treated as ordinary files. Python refuses both containers, but preparation accepts and preserves both."
      },
      "repro_python": "z=io.BytesIO()\nwith zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as a:a.writestr('x',b'qwen')\nbad_zip=b'#!/usr/bin/env python3\\n'+z.getvalue()[:-22]\nraw=io.BytesIO()\nwith tarfile.open(fileobj=raw,mode='w',format=tarfile.USTAR_FORMAT) as a:\n b=gzip.compress(b'qwen');m=tarfile.TarInfo('x.gz');m.size=len(b);a.addfile(m,io.BytesIO(b))\nbad_tar=bytearray(raw.getvalue());bad_tar[257:265]=b'\\0'*8;bad_tar[148:156]=b'0000000\\0'\nfor name,blob in [('a.zip',bad_zip),('a.tar',bytes(bad_tar))]:\n try:\n  if name.endswith('.zip'):zipfile.ZipFile(io.BytesIO(blob))\n  else:tarfile.open(fileobj=io.BytesIO(blob),mode='r:')\n except Exception as e:print(name,type(e).__name__)\n accepted(name,blob)",
      "output": [
        "a.zip BadZipFile",
        "a.zip hits [] prepare ACCEPTED unchanged True",
        "a.tar ReadError",
        "a.tar hits [] prepare ACCEPTED unchanged True"
      ],
      "expect": "Refuse recognizable damaged containers, including prefixed ZIPs and tar files without ustar magic."
    },
    {
      "id": "OC-25",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/ANON_WORDS.txt",
      "line_start": 7,
      "line_end": 7,
      "text": {
        "status": "not fixed",
        "detail": "The specification forbids every listed word in any kit file. The name-only split rule explicitly exempts ordinary file contents. A file containing exactly split passes preparation and ships unchanged."
      },
      "repro_python": "accepted('a.txt',b'split')",
      "output": [
        "a.txt hits [] prepare ACCEPTED unchanged True"
      ],
      "expect": "Apply the stated prohibition to file contents as well as names."
    },
    {
      "id": "OC-26",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 482,
      "line_end": 507,
      "text": {
        "status": "not fixed",
        "detail": "The minted ledger identities do not bind all shipped bytes. JOB.json sessions can change after minting, and an unpinned DRYRUN_REPORT.json can be added to PREP/kit. Updating the generated scripts and their self-declared hashes allows both substitutions through submit with the original minted row unchanged. The JOB variant changes the result-upload destination."
      },
      "repro_python": "for change in ('JOB','DRYRUN'):\n files,c=fixture()\n with environment(files):\n  record=prep(files);row=anchor(record);job=util.read_json('/v/prep/JOB.json')\n  if change=='JOB':\n   job['sessions']={'result.tar.gz':'https://example.invalid/new-session'}\n   files['/v/prep/JOB.json']=util.canonical_json(job)\n  else:files['/v/prep/kit/DRYRUN_REPORT.json']=b'{\"note\":\"new unminted bytes\"}'\n  batch,remote=launch.build_submission('/v/prep/kit',c,job,rules)\n  files['/v/prep/BATCH.sh']=batch.encode();files['/v/prep/SUBMIT.sh']=remote.encode()\n  record.update(script_sha256=util.sha256_bytes(batch.encode()),submit_sha256=util.sha256_bytes(remote.encode()))\n  files['/v/prep/SUBMIT.json']=util.canonical_json(record);files['/v/GO']=('GO '+T).encode();sent=[]\n  with patch.object(ledger,'read_rows',return_value=[row]):\n   result=launch.submit('/v/prep','/v/GO',execute=True,ledger_file='/v/ledger',transport=lambda a,b:(sent.append(b) or (0,b'JOBID=4242\\n',b'')),out=io.StringIO())\n  print(change,result['status'],'calls',len(sent),'minted_hashes_unchanged',(row['kit_pins_sha256'],row['config_sha256'])==(record['kit_pins_sha256'],record['config_sha256']))",
      "output": [
        "JOB SUBMITTED calls 1 minted_hashes_unchanged True",
        "DRYRUN SUBMITTED calls 1 minted_hashes_unchanged True"
      ],
      "expect": "Anchor JOB.json and every shipped kit file to trusted minted evidence before accepting regenerated scripts."
    }
  ],
  "reproduction_context": {
    "instructions": "Run python_prelude followed by a finding's repro_python in a fresh Python process. The prelude reuses the permitted VERDICT_6 fixture and adapts its filesystem mocks for current locks and unique snapshots. No filesystem writes or real submissions occur.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools",
      "PYTHONDONTWRITEBYTECODE": "1"
    },
    "python_prelude": "import io,os,json,gzip,tarfile,zipfile,ast\nfrom unittest.mock import patch\np='/scratch/jjyeung/orch_n30/e_orchkit-core/work/review/VERDICT_6.json.md'\nexec(json.JSONDecoder().raw_decode(open(p).read())[0]['reproduction_context']['python_prelude'])\nold_environment=environment\ndef environment(files):\n s=old_environment(files);opening=os.open;paths={};locks={};counter=[0]\n def op(path,flags,*args):\n  fd=opening(path,flags,*args);paths[fd]=path;return fd\n def flock(fd,mode):\n  path=paths[fd]\n  if mode & launch.fcntl.LOCK_UN:locks.pop(path,None)\n  elif path in locks:raise BlockingIOError(path)\n  else:locks[path]=fd\n def temporary(**kw):\n  counter[0]+=1;return '/v/check%d'%counter[0]\n for obj,name,value in [(os,'open',op),(os,'close',lambda fd:None),(launch.fcntl,'flock',flock),(launch.tempfile,'mkdtemp',temporary)]:\n  s.enter_context(patch.object(obj,name,value))\n return s\ndef anchor(r):\n return ledger.make_row('minted',r['token'],kit_pins_sha256=r['kit_pins_sha256'],config_sha256=r['config_sha256'],partition=r['partition'])\ndef accepted(name,blob):\n files,c=fixture({name:blob})\n with environment(files):\n  hits=anon.scan_tree('/v/kit',rules);prep(files)\n  print(name,'hits',hits,'prepare ACCEPTED','unchanged',payload(files)['kit/'+name]==blob)\n"
  }
}

OC-01..OC-21 pass their reproduced cases. Five new blocking findings remain.
The partition lock works with unchanged metadata; mutable partition metadata bypasses it.
No files changed or jobs submitted.