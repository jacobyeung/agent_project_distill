#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a89e8fdab55d4
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
