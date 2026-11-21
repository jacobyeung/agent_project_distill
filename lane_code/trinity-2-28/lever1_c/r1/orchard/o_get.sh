#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a3b73b53d92a7
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
