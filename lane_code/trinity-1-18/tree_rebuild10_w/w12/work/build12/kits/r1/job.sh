#!/bin/bash
set -eu
umask 077
exec python3 -I -s -B b/a.py t "$1"
