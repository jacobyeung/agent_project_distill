#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a5d31c07be9f2
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
