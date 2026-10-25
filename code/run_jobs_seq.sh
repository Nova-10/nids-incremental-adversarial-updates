#!/bin/bash
cd /home/claude/matched
cat jobs_seq.txt | xargs -P 2 -I{} bash -c 'python3 run_matched_seq.py --rounds 5 --max-train 0 --epochs 5 --control-arm --matched-arms {} > /dev/null 2>>errors_seq.log && echo "DONE {}" || echo "FAIL {}"' >> seq_log.txt
echo ALLDONE >> seq_log.txt
