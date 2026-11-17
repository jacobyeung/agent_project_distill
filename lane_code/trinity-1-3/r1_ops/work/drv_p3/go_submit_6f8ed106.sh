#!/bin/bash
set +x
echo "REFUSED: this driver set authorizes only the S2-on CPU proof; production requires separate identity-bound authorization and tooling" >&2
exit 4
