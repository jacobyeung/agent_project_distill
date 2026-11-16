{
  "schema": "orchkit-verdict-v1",
  "utc": "2026-11-16T13:55:05Z",
  "reviewer_lane": "codex_review_orchkit_core_5",
  "requested_head": "cb6a5f04",
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
    "method": "Reran OC-01 through OC-14. Adapted filesystem mocks for snapshot creation and supplied matching minted-row identities for the strengthened submit checks. Actual preparation, scanning, hashing, bundling and submission validation ran; filesystem mutations and transport were mocked.",
    "unit_test_output": "Ran 1 test in 0.002s\nOK",
    "full_suite": "Not run: the filesystem is read-only, and some suite fixtures read outside the permitted paths.",
    "baseline_comparison": "Reconstructed pre-FIX_4 launch.py and anon.py in memory, checking the reversed hunks against current source. OC-15 is introduced by FIX_4; OC-16 and OC-17 also reproduce before it.",
    "side_effects": "No files changed. No Git, SSH, Slurm or network commands ran. OC-05 used a local shell function named squeue. No jobs were actually submitted."
  },
  "reproduction_context": {
    "instructions": "For each new finding, execute python_prelude followed by repro_python using /usr/bin/python3 -B -c. The prelude reuses VERDICT_4's in-memory fixtures and adapts their filesystem operations to exercise the actual snapshot implementation.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools"
    },
    "python_prelude": "import gzip,json\nwith open('/scratch/jjyeung/orch_n30/e_orchkit-core/work/review/VERDICT_4.json.md') as f:\n v=json.JSONDecoder().raw_decode(f.read())[0]\nexec(v['reproduction_context']['python_prelude'])\nbase_environment=environment\ndef environment(files):\n stack=base_environment(files);fds={}\n class Writer(FD):\n  def __init__(self,path):super().__init__();self.path=path\n  def close(self):\n   if not self.closed:files[self.path]=self.getvalue()\n   super().close()\n def opening(path,flags,*a):\n  if flags & os.O_EXCL and path in files:raise FileExistsError(path)\n  files[path]=b'';fd=100+len(fds);fds[fd]=path;return fd\n def rename(src,dst):\n  for p in list(files):\n   if p.startswith(src+'/'):files[dst+p[len(src):]]=files.pop(p)\n for obj,name,value in [(launch.tempfile,'mkdtemp',lambda **k:'/v/check'),(os.path,'isdir',lambda p:True),(os,'walk',lambda root:[(root,[],sorted(os.path.basename(p) for p in files if os.path.dirname(p)==root))]),(os,'open',opening),(os,'fdopen',lambda fd,*a:Writer(fds[fd])),(os,'rename',rename)]:\n  stack.enter_context(patch.object(obj,name,value))\n return stack\ndef minted(record):\n return ledger.make_row('minted',T,kit_pins_sha256=record['kit_pins_sha256'],config_sha256=record['config_sha256'])\n"
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
        "detail": "The original text-only helper calls still return empty results. Current prepare rejects each original forbidden root, environment and pool fixture."
      },
      "output": [
        "schema []",
        "config_hits []",
        "batch_hits []",
        "submit_hits []",
        "actual_env_hits 2",
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
        "detail": "mint_job_name rejects the token containing a trailing newline."
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
        "OC-06 requested=[104857600] exit=3 accepted=False"
      ]
    },
    {
      "id": "OC-07",
      "text": {
        "status": "fixed",
        "detail": "The deterministic interleaving at exclusive intent creation permits only one transport call."
      },
      "output": [
        "race transport_calls_same_token 1 altered_bytes_sent False approved_bytes_sent True errors ['submission UNCERTAIN: ', 'another submit of 0123456789abcdef holds the intent; never repeat a submit']"
      ]
    },
    {
      "id": "OC-08",
      "text": {
        "status": "fixed",
        "detail": "Replacing SUBMIT.sh at intent creation cannot change the verified bytes sent. Replacing it after _load_prep causes refusal."
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
        "detail": "The original compression-header hash produces a single-place violation, and prepare refuses it."
      },
      "output": [
        "after opacity_hits []",
        "after single_place [{'where': 'a.bin', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]",
        "OC-10 prepare REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.bin\"}]"
      ]
    },
    {
      "id": "OC-11",
      "text": {
        "status": "fixed",
        "detail": "Replacing the source file during provenance leaves the checked snapshot and bundled bytes unchanged."
      },
      "output": [
        "OC-11 status SUBMITTED transport_calls 1 shipped_data b'ok'"
      ]
    },
    {
      "id": "OC-12",
      "text": {
        "status": "fixed",
        "detail": "The original token-only metadata substitution is refused before transport. OC-16 documents a separate remaining metadata bypass."
      },
      "output": [
        "OC-12 REFUSED the prepared scripts do not belong to token fedcba9876543210 transport_calls 0"
      ]
    },
    {
      "id": "OC-13",
      "text": {
        "status": "fixed",
        "detail": "Both the ordinary and prefixed ZIP fixtures are inspected and refused."
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
        "detail": "Duplicate-key values, root strings and UTF-16 hashes are detected. Actual prepare refuses all three fixtures."
      },
      "output": [
        "single_place duplicate_key REFUSED single-place invariant: [{\"field\": \"x\", \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.json\"}]",
        "single_place root_string REFUSED single-place invariant: [{\"field\": \"\", \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.json\"}]",
        "single_place utf16 REFUSED single-place invariant: [{\"field\": null, \"reason\": \"copy of a pinned hash outside PINS.json\", \"value\": \"2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df\", \"where\": \"a.txt\"}]"
      ]
    },
    {
      "id": "OC-15",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 97,
      "line_end": 103,
      "introduced_by_fix_4": true,
      "text": {
        "status": "not fixed",
        "detail": "The new ZIP fallback takes precedence over tar inspection. Appending an empty ZIP to a tar containing a gzip member makes the scanner inspect only the empty ZIP. The tar remains readable, but its compressed member is skipped. Actual prepare accepts and preserves both a forbidden-word fixture and a duplicate-pinned-hash fixture. Both checks detect their respective violations before FIX_4."
      },
      "repro_python": "for label,secret in [('opacity',b'qwen'),('single_place',util.sha256_bytes(b'ok').encode())]:\n raw=io.BytesIO()\n with tarfile.open(fileobj=raw,mode='w') as a:\n  b=gzip.compress(secret);m=tarfile.TarInfo('x.gz');m.size=len(b);a.addfile(m,io.BytesIO(b))\n z=io.BytesIO()\n with zipfile.ZipFile(z,'w'):pass\n files,c=fixture({'a.bin':raw.getvalue()+z.getvalue()})\n with environment(files):\n  print(label,'current opacity',anon.scan_tree('/v/kit',rules),'single_place',pins.check_single_place('/v/kit'))\n  old=lambda data:next((kind for magic,kind in anon.MAGIC if data.startswith(magic)),None)\n  with patch.object(anon,'_compression',old):\n   print(label,'before_FIX4 opacity',anon.scan_tree('/v/kit',rules),'single_place',pins.check_single_place('/v/kit'))\n  prep(files)\n  with tarfile.open(fileobj=io.BytesIO(payload(files)['kit/a.bin']),mode='r:') as a:decoded=gzip.decompress(a.extractfile('x.gz').read())\n  print(label,'current prepare ACCEPTED decoded',repr(decoded))\n",
      "output": [
        "opacity current opacity [] single_place []",
        "opacity before_FIX4 opacity [{'where': 'a.bin!/x.gz!gz', 'scope': 'text', 'rule': 'rule 19'}] single_place []",
        "opacity current prepare ACCEPTED decoded b'qwen'",
        "single_place current opacity [] single_place []",
        "single_place before_FIX4 opacity [] single_place [{'where': 'a.bin!/x.gz!gz', 'field': None, 'value': '2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df', 'reason': 'copy of a pinned hash outside PINS.json'}]",
        "single_place current prepare ACCEPTED decoded b'2689367b205c16ce32ed4200942b8b8b1e262dfc70d9bc9fbc77c49699a4f1df'"
      ],
      "expect": "Inspect every supported archive interpretation or reject ambiguous archives before preparation succeeds."
    },
    {
      "id": "OC-16",
      "severity": "blocker",
      "class": "admission",
      "file": "tools/orchkit/launch.py",
      "line_start": 444,
      "line_end": 514,
      "introduced_by_fix_4": false,
      "text": {
        "status": "not fixed",
        "detail": "Submit still trusts mutable command arguments and self-declared script hashes in SUBMIT.json. Appending another sbatch command to SUBMIT.sh and updating submit_sha256 passes all checks: the original job-name line and batch digest remain present, and the ledger's kit/config identities still match. Changing only argv's remote-command argument also passes. Both variants dispatch a command containing qwen and a second token absent from the GO. Transport was captured and mocked; the injected commands were not executed."
      },
      "repro_python": "for change in ['script','argv']:\n files,c=fixture()\n with environment(files):\n  record=prep(files)\n  injected=\"sbatch --job-name=\"+launch.PREFIX+U+\" --wrap='echo qwen'\\n\"\n  if change=='script':\n   files['/v/prep/SUBMIT.sh']+=injected.encode()\n   record['submit_sha256']=util.sha256_bytes(files['/v/prep/SUBMIT.sh'])\n  else:record['argv'][-1]='bash -s; '+injected.strip()\n  files['/v/prep/SUBMIT.json']=util.canonical_json(record);files['/v/GO']=('GO '+T).encode();sent=[]\n  with patch.object(ledger,'read_rows',return_value=[minted(record)]):\n   result=launch.submit('/v/prep','/v/GO',execute=True,ledger_file='/v/ledger',transport=lambda a,b:(sent.append((a,b)) or (0,b'JOBID=4242\\n',b'')),out=io.StringIO())\n  dispatched=sent[0][1] if change=='script' else sent[0][0][-1].encode()\n  print(change,'status',result['status'],'GO_names_extra_token',launch._names(files['/v/GO'].decode(),U),'injected_command_sent',injected.strip().encode() in dispatched)\n",
      "output": [
        "script status SUBMITTED GO_names_extra_token False injected_command_sent True",
        "argv status SUBMITTED GO_names_extra_token False injected_command_sent True"
      ],
      "baseline_output": [
        "before_FIX4 script status SUBMITTED GO_names_extra_token False injected_command_sent True",
        "before_FIX4 argv status SUBMITTED GO_names_extra_token False injected_command_sent True"
      ],
      "expect": "Bind the complete submission script and transport command to trusted preparation evidence; refuse altered commands before dispatch."
    },
    {
      "id": "OC-17",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 303,
      "line_end": 310,
      "introduced_by_fix_4": false,
      "text": {
        "status": "not fixed",
        "detail": "The JSON name scan discards earlier duplicate-key values. Prepending a duplicate job object containing root_parent=/tmp/split leaves the final parsed configuration valid, while the forbidden path remains in the original CONFIG.json bytes. The raw text scan does not apply the name-only split rule. Actual prepare accepts and bundles the forbidden path unchanged."
      },
      "repro_python": "files,c=fixture()\nfiles['/v/kit/CONFIG.json']=files['/v/kit/CONFIG.json'].replace(b'\"job\":',b'\"job\":{\"root_parent\":\"/tmp/split\"},\"job\":')\nwith environment(files):\n print('duplicate_config opacity',anon.scan_tree('/v/kit',rules))\n prep(files)\n print('duplicate_config prepare ACCEPTED preserved',b'/tmp/split' in payload(files)['kit/CONFIG.json'])\n",
      "output": [
        "duplicate_config opacity []",
        "duplicate_config prepare ACCEPTED preserved True"
      ],
      "baseline_output": [
        "before_FIX4 duplicate_config opacity []",
        "before_FIX4 duplicate_config prepare ACCEPTED preserved True"
      ],
      "expect": "Reject duplicate JSON keys or apply name checks to every key and value before duplicate values are discarded."
    }
  ]
}

OC-01 through OC-14 pass their original reproductions.
Three verified bypasses remain; OC-15 is a FIX_4 regression.
The verdict remains NO_GO.