#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a7e29d4c8f103
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
