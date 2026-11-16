{
  "schema": "orchkit-verdict-v1",
  "utc": "2026-11-16T14:07:59Z",
  "reviewer_lane": "codex_review_orchkit_core_6",
  "requested_head": "fbe5ece7",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "scope_files": [
    "tools/orchkit/",
    "work/review/VERDICT_1..5.json.md",
    "work/review/FIX_1..5.diff"
  ],
  "validation": {
    "method": "Reran all 17 original reproductions. Adapted filesystem mocks for snapshot creation and regular-file checks, and supplied matching minted ledger identities. Preparation, scanning, pin verification, bundling, rebuilding and submission gates ran against in-memory files. Transport and filesystem mutations were mocked.",
    "unit_test_output": "Ran 1 test in 0.002s\nOK",
    "full_suite": "Not run: its fixtures require filesystem writes and include reads outside the permitted paths.",
    "baseline_comparison": "Reconstructed pre-FIX_5 anon.py and launch.py in memory by reversing FIX_5 hunks, asserting each replacement matched exactly once.",
    "go_controls": [
      "NO_GO 0123456789abcdef: REFUSED",
      "GO fedcba9876543210: REFUSED",
      "GO: a15_cot_ap0123456789abcdef: SUBMITTED",
      "GO control total transport calls 1"
    ],
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. OC-05 used a local shell function named squeue. No jobs were submitted."
  },
  "reproduction_context": {
    "instructions": "For each new finding, execute python_prelude followed by repro_python in a fresh /usr/bin/python3 -B -c process. The prior verdict supplies the in-memory fixture; this prelude adapts its lstat mock to the current implementation.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools"
    },
    "python_prelude": "import json,os,stat,types\nwith open('/scratch/jjyeung/orch_n30/e_orchkit-core/work/review/VERDICT_5.json.md') as f:\n v=json.JSONDecoder().raw_decode(f.read())[0]\nexec(v['reproduction_context']['python_prelude'])\nprevious_environment=environment\ndef environment(files):\n stack=previous_environment(files)\n stack.enter_context(patch.object(os,'lstat',lambda p:types.SimpleNamespace(st_mode=stat.S_IFREG|0o600)))\n return stack\n"
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
        "detail": "The original text-only helper calls still return empty results. Actual prepare rejects each forbidden root, environment and pool fixture."
      },
      "output": [
        "schema []",
        "config_hits []",
        "batch_hits []",
        "submit_hits []",
        "actual_env_hits 2",
        "root: prepare REFUSED opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "env: prepare REFUSED opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]",
        "pool: prepare REFUSED opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]"
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
        "detail": "The token containing a trailing newline is rejected."
      },
      "output": [
        "LaunchError: token must be 16 lowercase hex: '0123456789abcdef\\n'"
      ]
    },
    {
      "id": "OC-05",
      "text": {
        "status": "fixed",
        "detail": "A failed scheduler query stops the generated gate."
      },
      "output": [
        "rc=6 stdout=LIVE unknown: squeue failed"
      ]
    },
    {
      "id": "OC-06",
      "text": {
        "status": "fixed",
        "detail": "The room check requests the full 100 MiB allocation and refuses the simulated 16 MiB remaining quota."
      },
      "output": [
        "SHORT home [Errno 122] Disk quota exceeded",
        "requested [104857600] exit 3"
      ]
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "The original race against one preparation directory permits only one transport call. OC-21 covers the distinct case of two copies of that directory."
      },
      "output": [
        "race transport_calls 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ', 'another submit of 0123456789abcdef holds the intent; never repeat a submit']"
      ]
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Replacing SUBMIT.sh at intent creation cannot change the bytes sent. Replacing it after _load_prep causes refusal."
      },
      "output": [
        "swap_at_intent transport_calls 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ']",
        "swap_after_load transport_calls 0 altered_bytes_sent False approved_bytes_sent False errors ['SUBMIT.sh differs from its rebuild; prepare again']"
      ]
    },
    {
      "id": "OC-09",
      "text": {
        "status": "fixed",
        "detail": "The gzip filename and both compressed-stream trailers produce opacity hits."
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
        "detail": "The compression-header hash produces a single-place violation, and prepare refuses it."
      },
      "output": [
        "after opacity_hits []",
        "after single_place [{'where': 'a.bin', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]",
        "prepare REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.bin\"}]"
      ]
    },
    {
      "id": "OC-11",
      "text": {
        "status": "fixed",
        "detail": "Replacing the source file during provenance leaves the preparation snapshot unchanged. OC-20 covers a separate race during submit's new rebuild."
      },
      "output": [
        "OC-11 status SUBMITTED transport_calls 1 shipped_data b'ok'"
      ]
    },
    {
      "id": "OC-12",
      "text": {
        "status": "fixed",
        "detail": "The original token-only metadata substitution is refused."
      },
      "output": [
        "REFUSED the prepared scripts do not belong to token fedcba9876543210"
      ]
    },
    {
      "id": "OC-13",
      "text": {
        "status": "fixed",
        "detail": "Both ordinary and prefixed ZIP fixtures are inspected and refused."
      },
      "output": [
        "prefix_zip False hits [{'where': 'a.zip!/x', 'scope': 'text', 'rule': 'rule 19'}]",
        "prefix_zip prepare REFUSED opacity: [{\"rule\": \"rule 19\", \"scope\": \"text\", \"where\": \"a.zip!/x\"}]",
        "prefix_zip True hits [{'where': 'a.zip!/x', 'scope': 'text', 'rule': 'rule 19'}]",
        "prefix_zip prepare REFUSED opacity: [{\"rule\": \"rule 19\", \"scope\": \"text\", \"where\": \"a.zip!/x\"}]"
      ]
    },
    {
      "id": "OC-14",
      "text": {
        "status": "fixed",
        "detail": "Duplicate-key values, root strings and UTF-16 hashes are detected. Actual prepare refuses all three."
      },
      "output": [
        "single_place duplicate_key REFUSED single-place invariant: [{\"field\": \"x\", \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.json\"}]",
        "single_place root_string REFUSED single-place invariant: [{\"field\": \"\", \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.json\"}]",
        "single_place utf16 REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.txt\"}]"
      ]
    },
    {
      "id": "OC-15",
      "text": {
        "status": "fixed",
        "detail": "Appending an empty ZIP no longer hides the tar interpretation. Both original violations are detected and refused."
      },
      "output": [
        "opacity current opacity [{'where': 'a.bin!/x.gz!gz', 'scope': 'text', 'rule': 'rule 19'}] single_place []",
        "prepare REFUSED opacity: [{\"rule\": \"rule 19\", \"scope\": \"text\", \"where\": \"a.bin!/x.gz!gz\"}]",
        "single_place current opacity [] single_place [{'where': 'a.bin!/x.gz!gz', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]",
        "prepare REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.bin!/x.gz!gz\"}]"
      ]
    },
    {
      "id": "OC-16",
      "text": {
        "status": "fixed",
        "detail": "Both original command substitutions are refused before transport."
      },
      "output": [
        "script REFUSED SUBMIT.sh differs from its rebuild; prepare again transport_calls 0",
        "argv REFUSED the transport command differs from the one prepare recorded transport_calls 0"
      ]
    },
    {
      "id": "OC-17",
      "text": {
        "status": "fixed",
        "detail": "The forbidden path in the discarded duplicate CONFIG.json value is detected and refused."
      },
      "output": [
        "duplicate_config opacity [{'where': 'CONFIG.json', 'scope': 'name', 'rule': 'rule 7'}]",
        "REFUSED opacity: [{\"rule\": \"rule 7\", \"scope\": \"name\", \"where\": \"CONFIG.json\"}]"
      ]
    },
    {
      "id": "OC-18",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 335,
      "line_end": 341,
      "introduced_by_fix_5": false,
      "text": {
        "status": "not fixed",
        "detail": "JSON escape inspection requires a .json suffix and UTF-8 decoding. Valid UTF-16 and UTF-32 JSON, gzip-compressed JSON, and JSON stored without that suffix bypass it. Each reproduced file decodes to qwen using standard Python decoders, passes actual prepare and ships unchanged. FIX_5 adds JSON escape inspection but leaves these standard representations uncovered."
      },
      "repro_python": "plain=b'{\"m\":\"q\\\\u0077en\"}'\nfor label,name,blob in [('utf16','a.json',plain.decode().encode('utf-16')),('utf32','a.json',plain.decode().encode('utf-32')),('gzip_json','a.json.gz',gzip.compress(plain)),('json_without_extension','a.bin',plain)]:\n files,c=fixture({name:blob})\n with environment(files):\n  hits=anon.scan_tree('/v/kit',rules);prep(files)\n  shipped=payload(files)['kit/'+name]\n  decoded=json.loads(gzip.decompress(shipped) if label=='gzip_json' else shipped)\n  print(label,'opacity',hits,'prepare ACCEPTED','decoded',decoded,'bundled_unchanged',shipped==blob)\n",
      "output": [
        "utf16 opacity [] prepare ACCEPTED decoded {'m': 'qwen'} bundled_unchanged True",
        "utf32 opacity [] prepare ACCEPTED decoded {'m': 'qwen'} bundled_unchanged True",
        "gzip_json opacity [] prepare ACCEPTED decoded {'m': 'qwen'} bundled_unchanged True",
        "json_without_extension opacity [] prepare ACCEPTED decoded {'m': 'qwen'} bundled_unchanged True"
      ],
      "baseline_output": [
        "a.json before_FIX5 [] after_FIX5 []",
        "a.json.gz before_FIX5 [] after_FIX5 []"
      ],
      "expect": "Inspect JSON escapes across the supported text encodings and compression layers without relying exclusively on a filename suffix."
    },
    {
      "id": "OC-19",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 106,
      "line_end": 113,
      "introduced_by_fix_5": true,
      "text": {
        "status": "not fixed",
        "detail": "FIX_5 removes recognition of ZIP signatures unless is_zipfile succeeds. Removing the end-of-central-directory record from a deflated ZIP makes Python refuse the container, but the scanner treats it as an ordinary file. Actual prepare accepts and preserves it. This violates the explicit requirement that containers Python cannot open fail closed; the pre-FIX_5 scanner rejects the same bytes."
      },
      "repro_python": "z=io.BytesIO()\nwith zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as a:a.writestr('x',b'qwen')\nblob=z.getvalue()[:-22];files,c=fixture({'a.zip':blob})\ntry:zipfile.ZipFile(io.BytesIO(blob))\nexcept zipfile.BadZipFile as e:print('truncated_zip Python',type(e).__name__,str(e))\nwith environment(files):\n print('truncated_zip opacity',anon.scan_tree('/v/kit',rules))\n prep(files);print('truncated_zip prepare ACCEPTED bundled_unchanged',payload(files)['kit/a.zip']==blob)\n",
      "output": [
        "truncated_zip Python BadZipFile File is not a zip file",
        "truncated_zip opacity []",
        "truncated_zip prepare ACCEPTED bundled_unchanged True"
      ],
      "baseline_output": [
        "truncated_zip before_FIX5 [{'where': 'a.zip', 'scope': 'size', 'rule': 'undecodable'}]",
        "truncated_zip after_FIX5 []"
      ],
      "expect": "Retain fail-closed recognition of damaged ZIP containers while supporting prefixed ZIPs."
    },
    {
      "id": "OC-20",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 493,
      "line_end": 503,
      "fix_5_relation": "The new rebuild path validates kit files and then reopens them for bundling. The reproduction's mutation occurs at the intervening JOB.json read.",
      "text": {
        "status": "not fixed",
        "detail": "Submit's rebuild does not bind validation to the bytes it bundles. After check_kit verifies the ledger-anchored pins, replacing PREP/kit/data.bin and updating BATCH.sh and SUBMIT.sh to the resulting rebuild passes the remaining comparisons. The submitted payload contains qwen while PINS.json still identifies b'ok'. The minted ledger row remains unchanged. This is separate from OC-11's source-kit mutation during prepare."
      },
      "repro_python": "files,c=fixture()\nwith environment(files):\n record=prep(files);files['/v/GO']=('GO '+T).encode();sent=[];original_read=util.read_json;swapped=[False]\n def read_then_swap(path):\n  value=original_read(path)\n  if path=='/v/prep/JOB.json' and not swapped[0]:\n   swapped[0]=True;files['/v/prep/kit/data.bin']=b'qwen'\n   script,remote=launch.build_submission('/v/prep/kit',c,value,rules)\n   files['/v/prep/BATCH.sh']=script.encode();files['/v/prep/SUBMIT.sh']=remote.encode()\n  return value\n with patch.object(ledger,'read_rows',return_value=[minted(record)]),patch.object(util,'read_json',read_then_swap):\n  result=launch.submit('/v/prep','/v/GO',execute=True,ledger_file='/v/ledger',transport=lambda a,b:(sent.append(b) or (0,b'JOBID=4242\\n',b'')),out=io.StringIO())\n shipped=payload(files)\n p=json.loads(shipped['kit/PINS.json'])\n digest=next(e['sha256'] for e in p['entries'] if e['logical_path']=='data.bin')\n print('status',result['status'],'transport_calls',len(sent),'shipped_data',repr(shipped['kit/data.bin']),'matches_pin',util.sha256_bytes(shipped['kit/data.bin'])==digest,'remote_sent',sent[0].endswith(files['/v/prep/SUBMIT.sh']))\n",
      "output": [
        "status SUBMITTED transport_calls 1 shipped_data b'qwen' matches_pin False remote_sent True"
      ],
      "baseline_output": [
        "status SUBMITTED transport_calls 1 shipped_data b'ok' matches_pin True remote_sent True"
      ],
      "baseline_note": "The identical callback does not fire before FIX_5 because the old submit does not read PREP/JOB.json. This comparison concerns the new race location, not the absence of other pre-FIX_5 submission bypasses.",
      "expect": "Validate and bundle one stable set of bytes, and compare that set with the minted ledger identities before transport."
    },
    {
      "id": "OC-21",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 536,
      "line_end": 553,
      "introduced_by_fix_5": false,
      "text": {
        "status": "not fixed",
        "detail": "The exclusive intent belongs to a preparation directory rather than the token. Two copies of one valid preparation can each claim an intent and pass the shared ledger check before either submission is recorded. A deterministic interleaving reaches transport twice and appends two submitted rows for the same token. The reproduction uses advanced to isolate the duplicate-token gate from the one-job partition gate; it never rewrites existing ledger rows."
      },
      "repro_python": "files,c=fixture(change=lambda c:c['job'].update(partition='advanced'))\nwith environment(files):\n record=prep(files);files['/v/GO']=('GO '+T).encode()\n for p,b in list(files.items()):\n  if p.startswith('/v/prep/'):files[p.replace('/v/prep/','/v/copy/',1)]=b\n rows=[minted(record)];sent=[];results=[]\n def run(path):\n  r=launch.submit(path,'/v/GO',execute=True,ledger_file='/v/ledger',transport=transport,out=io.StringIO());results.append(r['status'])\n def transport(a,b):\n  sent.append(b);number=len(sent)\n  if number==1:run('/v/copy')\n  return 0,('JOBID=%d\\n'%(4240+number)).encode(),b''\n with patch.object(ledger,'read_rows',side_effect=lambda *a:rows[:]),patch.object(ledger,'append',side_effect=lambda row,*a:rows.append(row)):run('/v/prep')\n print('transport_calls_same_token',len(sent),'results',results,'ledger_submitted_rows',sum(r['event']=='submitted' for r in rows),'both_intents_exist',all(p in files for p in ['/v/prep/SUBMIT_INTENT.json','/v/copy/SUBMIT_INTENT.json']))\n",
      "output": [
        "transport_calls_same_token 2 results ['SUBMITTED', 'SUBMITTED'] ledger_submitted_rows 2 both_intents_exist True"
      ],
      "baseline_output": [
        "transport_calls_same_token 2 results ['SUBMITTED', 'SUBMITTED'] ledger_submitted_rows 2 both_intents_exist True"
      ],
      "expect": "Claim each token atomically through shared trusted state before transport, independently of the preparation directory."
    }
  ]
}

OC-01 through OC-17 pass their original reproductions.
Four additional verified defects keep the verdict at NO_GO.
FIX_5 introduces the damaged-ZIP regression and the new rebuild race location.
One unit test passed; the full suite was not run.
No files changed or jobs submitted.