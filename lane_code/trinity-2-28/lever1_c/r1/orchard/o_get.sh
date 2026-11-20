#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a09fdd101cc93
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
