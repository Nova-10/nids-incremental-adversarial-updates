#!/bin/bash
# usage: run_jobs.sh jobsfile logfile
cd /home/claude/matched
cat "$1" | xargs -P 2 -I{} bash -c 'python3 run_matched.py --rounds 5 --max-train 0 --epochs 5 --control-arm --matched-arms {} > /dev/null 2>>errors.log && echo "DONE {}" || echo "FAIL {}"' >> "$2"
echo ALLDONE >> "$2"
