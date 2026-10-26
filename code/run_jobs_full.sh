#!/bin/bash
cd /home/claude/matched
cat jobs_full.txt | xargs -P 2 -I{} bash -c 'python3 run_matched_full.py --rounds 5 --max-train 0 --epochs 5 --control-arm --matched-arms {} > /dev/null 2>>errors_full.log && echo "DONE {}" || echo "FAIL {}"' >> full_log.txt
echo ALLDONE >> full_log.txt
