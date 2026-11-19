# lane_code_scan.py <stage> <dest> <flag list>: secret-scan every staged file; copy clean, changed files
# to <dest> (same relative path); flagged files are never copied and are listed as "<path>\t<pattern>".
import os, re, sys, shutil
stage, dest, flagout = sys.argv[1:4]
PATS = [
    ('private_key_block', re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
    ('aws_akia', re.compile(rb'AKIA[0-9A-Z]{16}')),
    ('hf_token', re.compile(rb'(?<![A-Za-z0-9])hf_[A-Za-z0-9]{30,}')),
    ('sk_key', re.compile(rb'(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{20,}')),
    ('github_token', re.compile(rb'(ghp|gho|ghs|ghu)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}')),
    ('google_api_key', re.compile(rb'AIza[0-9A-Za-z_\-]{30,}')),
    ('private_key_field', re.compile(rb'"private' rb'_key"')),
    ('url_credentials', re.compile(rb'[a-z][a-z0-9+.\-]{0,32}://[^\s/:@"\']+:[^\s/@"\'$]{6,}@')),
    ('url_token_param', re.compile(rb'[?&](token|access_token|api_key|apikey|key|sig|signature)=[A-Za-z0-9_\-%.]{16,}')),
    ('bearer_literal', re.compile(rb'Bearer\s+[A-Za-z0-9_\-.=]{20,}')),
    ('api_key_assign', re.compile(rb'(?<![A-Za-z0-9])(GEMINI|GOOGLE|OPENROUTER|NV|NVIDIA|ANTHROPIC|OPENAI|HF)_(API_)?(KEY|TOKEN)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{20,}')),
]
ENV_VALUES = [os.environ[k].encode() for k in ('GEMINI_API_KEY', 'GOOGLE_API_KEY', 'HF_TOKEN', 'OPENROUTER_API_KEY',
              'NV_API_KEY', 'NVIDIA_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY') if len(os.environ.get(k, '')) >= 16]
flags = []; copied = 0; same = 0; scanned = 0
for d, dirs, files in os.walk(stage):
    dirs.sort()
    for f in sorted(files):
        sp = os.path.join(d, f); rel = os.path.relpath(sp, stage)
        if os.path.islink(sp):
            continue
        try:
            data = open(sp, 'rb').read()
        except OSError:
            continue
        scanned += 1
        hit = [n for n, p in PATS if p.search(data)] + (['env_secret_value'] if any(v in data for v in ENV_VALUES) else [])
        if hit:
            flags.append('%s\t%s' % (rel, ','.join(hit))); continue
        dp = os.path.join(dest, rel)
        try:
            if open(dp, 'rb').read() == data:
                same += 1; continue
        except OSError:
            pass
        os.makedirs(os.path.dirname(dp), exist_ok=True)
        shutil.copyfile(sp, dp); copied += 1
os.makedirs(os.path.dirname(flagout), exist_ok=True)
open(flagout, 'w').write(''.join(x + '\n' for x in flags))
print('SCAN scanned=%d copied=%d unchanged=%d flagged=%d list=%s' % (scanned, copied, same, len(flags), flagout))
for x in flags[:50]:
    print('FLAG ' + x)
