#!/bin/bash
#
# Kills the specified process when a particular file is deleted.
#
# Usage:
#    ./terminator.sh <pid>

function usage() {
    echo "Usage: ./$0 <pid>"
}

if [[ "$#" != 1 ]] ; then
    usage
    exit 1
fi

if [[ "$1" == "--help" || "$1" == "-h" ]] ; then
    usage
    exit 0
fi

function process_alive() {
    kill -s 0 $1 2>/dev/null
}

pid=$1

if ! process_alive $pid ; then
    echo "No such pid ($pid)!"
    exit 1
fi

dir="/tmp/terminator"
if [[ ! -d "${dir}" ]] ; then
    mkdir -p ${dir}
    chmod og+w ${dir}
fi

file="${dir}/${USER}-${pid}"
touch ${file}
chmod og+w ${file}
echo "Watching file ${file}; if deleted, ${pid} will be killed."

group_pid="$(ps -o pgid= $pid | grep -o '[0-9]*')"
while true ; do
    if [[ ! -e ${file} ]] ; then
        echo "${file} deleted! Killing PID ${pid}."
        kill -SIGTERM -${group_pid}
        if process_alive ${pid} ; then
            sleep 30s
        fi
        if process_alive ${pid} ; then
            echo "Process didn't exit within 30s after SIGTERM." \
                "Sending SIGKILL."
            kill -SIGKILL -${group_pid}
        fi
        exit 1
    fi
    if ! process_alive ${pid} ; then
        echo "Process $pid exited on its own. Terminating terminator."
        rm ${file}
        exit 1
    fi
    sleep 30s
done
