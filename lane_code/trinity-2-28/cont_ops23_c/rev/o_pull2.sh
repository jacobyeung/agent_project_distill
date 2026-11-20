K=/project/community/jjyeung/okh7; cd $K
/usr/bin/python3 -B -c "import os;s=os.statvfs('$K');print('FREE_GIB %.2f'%(s.f_bavail*s.f_frsize/1024**3))" >&2
ls -la ae71c903/dd982cd5c4b250002a564 a15_cot_apdd982cd5c4b25/a >&2
tar cf - --exclude=a15_cot_apdd982cd5c4b25/a/e ae71c903/dd982cd5c4b250002a564 a15_cot_apdd982cd5c4b25/a
