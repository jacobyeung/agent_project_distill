"""Governed reader: stop before any IO, then run the given command with its stdout on this process's fd 1
(the pipe into ratelimit.py). One child, no retry. usage: cmd_reader.py CMD [ARGS...]"""
import os, signal, subprocess, sys
os.kill(os.getpid(), signal.SIGSTOP)
sys.exit(subprocess.run(sys.argv[1:], stdout=1).returncode)
