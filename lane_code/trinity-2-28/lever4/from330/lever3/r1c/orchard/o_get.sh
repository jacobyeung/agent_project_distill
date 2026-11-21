#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a38bd627f901e
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
