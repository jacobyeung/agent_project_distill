#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a4282fee306d6
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
