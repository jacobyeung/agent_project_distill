#!/usr/bin/env bash
# Shared Orchard connection per node. Usage: timeout 300 bash ossh.sh '<cmd>'  |  timeout 300 bash ossh.sh 'bash -s' < script.sh
exec ssh -o ControlMaster=auto -o ControlPath=/tmp/cm-n30-orchard-%r -o ControlPersist=60m -o ConnectTimeout=60 -o BatchMode=yes orchard "$@"
