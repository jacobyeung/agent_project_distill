#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/ad07f53341bc0
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
