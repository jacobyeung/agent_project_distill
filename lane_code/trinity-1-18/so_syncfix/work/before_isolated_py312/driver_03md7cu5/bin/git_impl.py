import json, os, sys
args = sys.argv[1:]
with open(os.environ['FAKE_GIT_LOG'], 'a') as f: f.write(json.dumps(args) + '\n')
if args[:1] == ['-C']: args = args[2:]
if args[:3] == ['diff', '--cached', '--quiet']: sys.exit(1)
if args[:3] == ['diff', '--cached', '--name-only']: print('lane_code/trinity-2-28/good.py')
elif args[:1] == ['rev-parse']: print('a' * 40)
elif args[:1] == ['ls-remote']: print('a' * 40 + '\trefs/heads/lane-code')
elif args[:1] not in (['add'], ['commit'], ['push']):
    raise SystemExit('unexpected fake Git call: ' + repr(args))
