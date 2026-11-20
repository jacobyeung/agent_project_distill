/usr/bin/python3 -B -c "import os;s=os.statvfs('/project/community/jjyeung/okh7');print('FREE_GIB %.2f'%(s.f_bavail*s.f_frsize/1024**3))"
du -sb /project/community/jjyeung/okh7/813f42db/c21h544r /project/community/jjyeung/okh7/ae71c903/dc863c3e6b41d0002a4ca 2>&1
ls /project/community/jjyeung/okh7/ae71c903/ | head -30
