import sys, re
src, M = sys.argv[1], sys.argv[2]
s = open(src).read()
parts = re.split(r'^@@FILE (\S+)\n', s, flags=re.M)
for i in range(1, len(parts), 2):
    open(f'{M}/{parts[i]}', 'w').write(parts[i + 1])
    print(parts[i], len(parts[i + 1]))
