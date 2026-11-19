#!/bin/bash
n=$(cat "$0.n" 2>/dev/null || echo 0); echo $((n+1)) > "$0.n"
case "$n" in
  *) echo "0, 22000, 0, 8.6" ;;
esac
