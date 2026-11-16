"""Governed GCS reader: stop before any network IO, then run `gsutil cat OBJECT` writing into this process's fd 1
(the pipe into ratelimit.py). One child, no retry. usage: gcs_reader.py gs://OBJECT"""
import os, signal, subprocess, sys
obj = sys.argv[1]
os.kill(os.getpid(), signal.SIGSTOP)
sys.exit(subprocess.run(['/home/jjyeung/google-cloud-sdk/bin/gsutil', '-q', 'cat', obj], stdout=1).returncode)
