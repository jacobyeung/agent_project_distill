#!/bin/bash
# Disk preflight. usage: preflight.sh DIR NEED_GB LABEL   -> exit 0 if DIR's filesystem has >= NEED_GB GiB free, else 1.
d=$1 need=$2 label=${3:-}
free=$(df -BG --output=avail "$d" 2>/dev/null | tail -1 | tr -dc 0-9)
if [ -n "$free" ] && [ "$free" -ge "$need" ]; then
  echo "PREFLIGHT_OK $label dir=$d free=${free}G need=${need}G"
else
  echo "PREFLIGHT_REFUSED $label dir=$d free=${free:-?}G need=${need}G"; exit 1
fi
