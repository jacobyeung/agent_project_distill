#!/bin/bash
# Run on Orchard login after o_build_E.sh. This script places and fills; it never submits.
set -euo pipefail
umask 077
: "${STAGE:?Set STAGE to the directory containing BUILD.json}"
# Optional: REUSE_PARTS_FROM holds verified parts 0,1,2,3; PREP_FROM holds 7,8,9 or config.json, prepared/s1_receipt.json, data_receipt.json.
# Optional: DONE_FROM is a three-field receipt; CLAIM_FROM contains the member name.
exec /usr/bin/python3 -B "$STAGE/place_fill_e.py" "$STAGE"
