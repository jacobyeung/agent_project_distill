#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a784b94c2e6af
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
