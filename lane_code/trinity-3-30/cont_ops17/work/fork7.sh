#!/bin/bash
# fork kit $1 -> $2: code real copies, big data dirs hardlinked (made read-only), no old builds
set -euo pipefail
S=$1; D=$2; cd /scratch/jjyeung/orch_n30/cont_ops/work
test -d $S && test ! -e $D
mkdir $D
for e in $S/* ; do
  n=$(basename $e)
  case $n in
    assets|evidence|readk|in|DIFF.md|DIFF.patch) cp -al $e $D/$n; find $D/$n -type f -perm /222 -exec chmod a-w {} + ;;
    kit) mkdir $D/kit; for k in $e/*; do b=$(basename $k); if [ $b = build ]; then mkdir $D/kit/build; else cp -a $k $D/kit/$b; fi; done ;;
    *) sz=$(du -s --apparent-size -m $e | cut -f1); if [ "$sz" -gt 20 ]; then cp -al $e $D/$n; find $D/$n -type f -perm /222 -exec chmod a-w {} +; echo "hardlinked $n ${sz}M"; else cp -a $e $D/$n; fi ;;
  esac
done
du -sh $D
