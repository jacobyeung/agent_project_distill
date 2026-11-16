#!/bin/bash
#
# Wrapper script for terminator.sh:
#
#   ./vnice.sh python train.py
#
# will launch train.py in the foreground, with a terminator in the background.
#
# Recommended usage is to add 'alias vnice=/path/to/vnice.sh' in your
# bashrc, and then run programs using:
#
#   vnice python train.py
#
# Note: If you have a complicated launch command that requires quotes, such as
#   vnice python train.py --cfg launch "['option1', 'option2']"
# this script may fail to respect the quotes. In these cases, either create
# a shell script that contains your command, or quote your entire command:
#   vnice "python train.py --cfg launch \"['option1', 'option2']\""
#
# Ideally, we could maintain quotes as passed to vnice, but I'm not sure how to
# do this. <https://stackoverflow.com/q/1668649/1291812> has some suggestions,
# if anyone wants to try them out. At the very least, it would be nice if this
# script errored when it saw quotes in the arguments that it could not respect.
# (-@achald, 11/14/18)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TERMINATOR="${DIR}/terminator.sh"

bash -c "${TERMINATOR} "'$$'" & exec ${*}"
