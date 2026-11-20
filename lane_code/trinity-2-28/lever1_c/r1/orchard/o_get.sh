#!/bin/bash
set -euo pipefail
P=/project/community/jjyeung/a6f198d3c7b20
tar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json
