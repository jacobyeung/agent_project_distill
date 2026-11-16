{
  "schema": "orchkit-verdict-v1",
  "reviewer_lane": "codex_review_orchkit_core_11",
  "requested_head": "73cc8638",
  "kit_pins_sha256": null,
  "verdict": "NO_GO",
  "validation": {
    "method": "Reran all 35 requested earlier reproductions with in-memory filesystem fixtures and mocked transport. Adapted submission fixtures for current snapshots, locks, minted payload identities and build_submission's return value.",
    "status_scope": "fixed means the original reproduced input now meets the specification. Additional bypasses appear separately.",
    "unit_tests": "JobNameTest: Ran 1 test in 0.002s; OK.",
    "full_suite": "Not run because the filesystem is read-only.",
    "controls": [
      "NO_GO and GO naming another token refused with zero transport calls.",
      "Correct GO accepted with one mocked transport call.",
      "Existing live job refused without correctly named queue-behind authorization.",
      "Remote live gate refused a failed query and an unauthorized live job; accepted an empty queue and correctly authorized queue-behind.",
      "Home and pool quota shortages refused after attempting the full budget allocation."
    ],
    "side_effects": "No files changed. No Git, SSH, real Slurm or network commands ran. Scheduler-query fixtures used local shell functions. No jobs were submitted."
  },
  "findings": [
    {
      "id": "OC-01",
      "text": {"status": "fixed", "detail": "All five original container and encoding fixtures are detected or refused."},
      "output": "disguised_gzip: rule 19; depth_five: too-deep; tar_uname: rule 19; fifo_bytes: rule 19 and special; utf16: rule 19"
    },
    {
      "id": "OC-02",
      "text": {"status": "fixed", "detail": "Preparation refuses each original root, environment and pool fixture."},
      "output": "root, env, pool: REFUSED CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-03",
      "text": {"status": "fixed", "detail": "Both original naming bypasses are detected."},
      "output": "ORCH_N30: rule 29; orchkit-pins-v1-private: rule 39"
    },
    {
      "id": "OC-04",
      "text": {"status": "fixed", "detail": "The trailing-newline token is refused; the job-name unit test passes."},
      "output": "LaunchError token must be 16 lowercase hex: '0123456789abcdef\\n'"
    },
    {
      "id": "OC-05",
      "text": {"status": "fixed", "detail": "A failed scheduler query stops the generated gate."},
      "output": "rc=6 stdout=LIVE unknown: squeue failed"
    },
    {
      "id": "OC-06",
      "text": {"status": "fixed", "detail": "The room check attempts the entire budget and refuses the simulated quota shortage."},
      "output": "home: SHORT, exit 3, allocated [104857600]; pool: SHORT, exit 3, allocated [104857600, 104857600]"
    },
    {
      "id": "OC-07",
      "text": {"status": "fixed", "detail": "Interleaving another submission before intent creation permits one transport call."},
      "output": "nested REFUSED another submission to this partition is in progress; first SUBMITTED; calls 1"
    },
    {
      "id": "OC-08",
      "text": {"status": "fixed", "detail": "Replacement after loading causes refusal; replacement at intent creation cannot change the rebuilt bytes sent."},
      "output": "after_load: REFUSED SUBMIT.sh differs from its rebuild, calls 0; at_intent: SUBMITTED, calls 1, altered_sent False"
    },
    {
      "id": "OC-09",
      "text": {"status": "fixed", "detail": "The original gzip filename and bz2/xz trailers are detected."},
      "output": "gzip_filename: rule 19; bz2_trailer and xz_trailer: rule 19 and undecodable"
    },
    {
      "id": "OC-10",
      "text": {"status": "fixed", "detail": "The pinned hash copied into a gzip header violates the single-place check."},
      "output": "a.bin and a.bin!gzip-header: copy of a pinned hash outside PINS.json"
    },
    {
      "id": "OC-11",
      "text": {"status": "fixed", "detail": "Changing the source kit during provenance leaves the checked snapshot unchanged."},
      "output": "SUBMITTED calls 1 shipped_data b'ok'"
    },
    {
      "id": "OC-12",
      "text": {"status": "fixed", "detail": "The token-only metadata substitution is refused."},
      "output": "REFUSED the prepared scripts do not belong to token fedcba9876543210; calls 0"
    },
    {
      "id": "OC-13",
      "text": {"status": "fixed", "detail": "Both ordinary and prefixed ZIP fixtures are inspected and refused."},
      "output": "Both fixtures: a.zip!/x rule 19; prepare REFUSED opacity"
    },
    {
      "id": "OC-14",
      "text": {"status": "fixed", "detail": "Duplicate-key values, root strings and UTF-16 copies of pinned hashes are detected."},
      "output": "duplicate_key, root_string, utf16: prepare REFUSED single-place invariant"
    },
    {
      "id": "OC-15",
      "text": {"status": "fixed", "detail": "An appended empty ZIP does not hide the tar interpretation."},
      "output": "opacity: REFUSED a.bin!/x.gz!gz rule 19; single_place: REFUSED duplicate pinned hash"
    },
    {
      "id": "OC-16",
      "text": {"status": "fixed", "detail": "Both original submission-script and transport-argument substitutions are refused."},
      "output": "script: REFUSED SUBMIT.sh differs from its rebuild; argv: REFUSED transport command differs; calls 0 for both"
    },
    {
      "id": "OC-17",
      "text": {"status": "fixed", "detail": "The forbidden path in the discarded duplicate CONFIG.json value is detected."},
      "output": "REFUSED CONFIG.json opacity rule 7"
    },
    {
      "id": "OC-18",
      "text": {"status": "fixed", "detail": "All four original Unicode-escape representations are detected."},
      "output": "utf16, utf32, gzip_json, json_without_extension: prepare REFUSED opacity rule 19"
    },
    {
      "id": "OC-19",
      "text": {"status": "fixed", "detail": "The original truncated ZIP is refused."},
      "output": "Python: BadZipFile; scanner: unsupported-container; prepare REFUSED unscannable"
    },
    {
      "id": "OC-20",
      "text": {"status": "fixed", "detail": "Changing PREP/kit/data.bin at the JOB.json read fails snapshot validation."},
      "output": "REFUSED pins differ: actual bytes 4, expected bytes 2; calls 0"
    },
    {
      "id": "OC-21",
      "text": {"status": "fixed", "detail": "Two preparation copies reach transport only once. The shared token claim also refuses reuse."},
      "output": "calls 1; submitted_rows 1; second claim REFUSED token 0123456789abcdef was already claimed"
    },
    {
      "id": "OC-22",
      "text": {"status": "fixed", "detail": "Partition metadata mutation causes refusal. The unchanged concurrent control permits one transport call."},
      "output": "control: calls 1, outcomes ['REFUSED', 'SUBMITTED']; mutation: REFUSED partition differs between config, ledger and SUBMIT.json, calls 0"
    },
    {
      "id": "OC-23",
      "text": {"status": "fixed", "detail": "The original octal, named-character and JSON slash escapes are detected."},
      "output": "octal.py and named.py: REFUSED rule 19; escaped slash: REFUSED rule 24"
    },
    {
      "id": "OC-24",
      "text": {"status": "fixed", "detail": "Both original damaged-container fixtures are refused."},
      "output": "prefixed ZIP and bad-checksum tar: prepare REFUSED unscannable (unsupported-container)"
    },
    {
      "id": "OC-25",
      "text": {"status": "resolved_by_specification", "detail": "The clarified rule permits split in ordinary file contents. This finding remains withdrawn."}
    },
    {
      "id": "OC-26",
      "text": {"status": "fixed", "detail": "Changing JOB.json sessions or adding an unminted DRYRUN_REPORT.json fails the whole-bundle payload comparison."},
      "output": "JOB and DRYRUN: REFUSED payload differs from the one its ledger row names; calls 0 for both"
    },
    {
      "id": "OC-27",
      "text": {"status": "fixed", "detail": "The original backslash-LF continuation is detected."},
      "output": "prepare REFUSED a.py opacity rule 19"
    },
    {
      "id": "OC-28",
      "text": {"status": "fixed", "detail": "The original gzip filename receives name checks."},
      "output": "prepare REFUSED a.gz!gzip-header name rule 7"
    },
    {
      "id": "OC-29",
      "text": {"status": "fixed", "detail": "The damaged tar with a UTF-8 filename is refused."},
      "output": "Python: ReadError bad checksum; prepare REFUSED unscannable"
    },
    {
      "id": "OC-30",
      "text": {"status": "fixed", "detail": "The original default LZMA-alone stream is inspected."},
      "output": "prepare REFUSED a.lzma!lzma opacity rule 19"
    },
    {
      "id": "OC-31",
      "text": {"status": "fixed", "detail": "The bare mount root and redundant leading slash are refused."},
      "output": "/data2 and //data2/secret: prepare REFUSED CONFIG.json opacity rule 24"
    },
    {
      "id": "OC-32",
      "text": {"status": "fixed", "detail": "The forbidden filename in the second concatenated gzip member is detected."},
      "output": "concat_gzip_fname: prepare REFUSED a.gz!gzip-header name rule 7"
    },
    {
      "id": "OC-33",
      "text": {"status": "fixed", "detail": "The original nondefault LZMA-alone property combinations are inspected."},
      "output": "lc=0,1,2,4: prepare REFUSED a.lzma!lzma opacity rule 19"
    },
    {
      "id": "OC-34",
      "text": {"status": "fixed", "detail": "The original smaller zlib window sizes are inspected."},
      "output": "wbits=9,10,14,15: prepare REFUSED a.zlib!zlib opacity rule 19"
    },
    {
      "id": "OC-35",
      "text": {"status": "fixed", "detail": "The original backslash-CR continuation is detected."},
      "output": "cr_continuation: prepare REFUSED a.py opacity rule 19"
    },
    {
      "id": "OC-36",
      "text": {"status": "fixed", "detail": "All four original dot-component paths are refused. OC-38 covers repeated-slash variants."},
      "output": "/./data2/secret and /tmp/../data2/secret: rule 24; /home/./jjyeung/agent_x: rule 25; /scratch/./jjyeung/x: rule 23; prepare REFUSED for all"
    },
    {
      "id": "OC-37",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 217,
      "line_end": 321,
      "text": {
        "status": "not fixed",
        "detail": "Damaged zlib and LZMA-alone containers pass preparation and submission. A zlib checksum error makes recognition fall through to ordinary-file scanning; truncated streams can return partial decoded content without an end-of-stream check. Python's standard decompressors refuse all three fixtures below, but the guards accept and preserve them."
      },
      "repro_python": "for label,blob,decode in [('bad_zlib',zlib.compress(b'qwen')[:-1]+b'X',zlib.decompress),('cut_zlib',zlib.compress(b'ok')[:-2],zlib.decompress),('cut_lzma',lzma.compress(b'ok',format=lzma.FORMAT_ALONE)[:-2],lzma.decompress)]:\n try:decode(blob)\n except Exception as e:print(label,'Python',type(e).__name__,str(e))\n files,c=fixture({'a.bin':blob});ship(label,files,'a.bin',blob)",
      "output": [
        "bad_zlib Python error Error -3 while decompressing data: incorrect data check",
        "bad_zlib hits []",
        "bad_zlib prepare ACCEPTED SUBMITTED calls 1 unchanged True",
        "cut_zlib Python error Error -5 while decompressing data: incomplete or truncated stream",
        "cut_zlib hits []",
        "cut_zlib prepare ACCEPTED SUBMITTED calls 1 unchanged True",
        "cut_lzma Python LZMAError Compressed data ended before the end-of-stream marker was reached",
        "cut_lzma hits []",
        "cut_lzma prepare ACCEPTED SUBMITTED calls 1 unchanged True"
      ],
      "expect": "Refuse recognizable damaged containers even when partial decompression succeeds."
    },
    {
      "id": "OC-38",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 85,
      "line_end": 98,
      "text": {
        "status": "not fixed",
        "detail": "Repeated slashes before a parent component defeat path normalization. The schema-valid root_parent /tmp//../data2/secret normalizes to /data2/secret but passes scanning, preparation and submission. The same bypass succeeds for /home/x//../jjyeung/agent_x and /scratch/x//../jjyeung/x."
      },
      "repro_python": "path='/tmp//../data2/secret'\nfiles,c=fixture(change=lambda c:c['job'].update(root_parent=path))\nprint('schema',launch.validate_config(c),'normpath',os.path.normpath(path))\nship('path',files,'CONFIG.json',files['/v/kit/CONFIG.json'])",
      "output": [
        "schema [] normpath /data2/secret",
        "path hits []",
        "path prepare ACCEPTED SUBMITTED calls 1 unchanged True"
      ],
      "expect": "Reject prohibited paths after ordinary lexical normalization, including repeated separators before parent components."
    },
    {
      "id": "OC-39",
      "severity": "blocker",
      "class": "legality",
      "file": "tools/orchkit/anon.py",
      "line_start": 121,
      "line_end": 138,
      "text": {
        "status": "not fixed",
        "detail": "text_views never decodes UTF-8. Consequently UTF-8 content can evade the existing Unicode case-insensitive rules: arKit matches the arkit rule when decoded, but its UTF-8 bytes pass scanning, preparation and submission. dİstill and gemİni also reproduce the discrepancy."
      },
      "repro_python": "blob='ar\\u212ait'.encode('utf-8')\nprint('decoded_hits',anon.scan_text('a.txt',blob.decode('utf-8'),rules),'byte_hits',anon.scan_bytes('a.txt',blob,rules))\nfiles,c=fixture({'a.txt':blob});ship('utf8',files,'a.txt',blob)",
      "output": [
        "decoded_hits [{'where': 'a.txt', 'scope': 'text', 'rule': 'rule 16'}] byte_hits []",
        "utf8 hits []",
        "utf8 prepare ACCEPTED SUBMITTED calls 1 unchanged True"
      ],
      "expect": "Apply the configured rules to the standard UTF-8 decoding as well as other supported text views."
    }
  ],
  "reproduction_context": {
    "instructions": "Run python_prelude followed by one new finding's repro_python in a fresh /usr/bin/python3 -B -c process. The permitted earlier verdict supplies the in-memory fixtures. SUBMITTED denotes mocked transport only.",
    "environment": {
      "TMPDIR": "/scratch/jjyeung/orch_n30/e_orchkit-core/tmp",
      "PYTHONPATH": "/scratch/jjyeung/orch_n30/e_orchkit-core/repo/tools"
    },
    "python_prelude": "import io,json,os,gzip,lzma,zlib,copy\nfrom unittest.mock import patch\nfrom orchkit import anon,launch,ledger\np='/scratch/jjyeung/orch_n30/e_orchkit-core/work/review/VERDICT_8.json.md'\nwith open(p) as f:v=json.JSONDecoder().raw_decode(f.read())[0]\nexec(v['reproduction_context']['python_prelude'])\nround11_environment=environment\ndef environment(files):\n s=round11_environment(files); rows=[]\n s.enter_context(patch.object(ledger,'read_rows',lambda *a:rows))\n s.enter_context(patch.object(ledger,'append',lambda row,*a,**k:rows.append(copy.deepcopy(row))))\n return s\ndef ship(label,files,name,blob):\n with environment(files):\n  print(label,'hits',anon.scan_tree('/v/kit',rules))\n  prep(files);files['/v/GO']=('GO '+T).encode();sent=[]\n  r=launch.submit('/v/prep','/v/GO',execute=True,ledger_file='/v/ledger',out=io.StringIO(),transport=lambda a,b:(sent.append(b) or (0,b'JOBID=4242\\n',b'')))\n  print(label,'prepare ACCEPTED',r['status'],'calls',len(sent),'unchanged',payload(files)['kit/'+name]==blob)"
  }
}

All 35 requested earlier reproductions meet the specification for their original inputs.
Three additional bypasses, OC-37–OC-39, require correction.