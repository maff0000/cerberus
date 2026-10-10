#!/bin/sh
# CD-ASR-WO2R3-06 — race TWO launch.sh invocations with DIFFERENT lease ids and THE SAME write scope.
# This is PO-DECISIONS-0021 ruling 2's incident, reproduced against the control built to stop it.
T=/tmp/cd-asr-wo2r3-06/race/tree
R=0; DBL=0; ONE=0; ZERO=0
for i in $(seq 1 60); do
  rm -f "$T"/governance/coordination/leases/*.lease.yaml
  ( sh "$T/tools/coordination/launch.sh" --lease "L$i-A" --seat SEAT-ALPHA --task "TASK-$i-A" \
      --write-scope 'governance/engineering/**' --dry-run -- true >/tmp/cd-asr-wo2r3-06/race/a.out 2>&1; echo $? > /tmp/cd-asr-wo2r3-06/race/a.rc ) &
  ( sh "$T/tools/coordination/launch.sh" --lease "L$i-B" --seat SEAT-BRAVO --task "TASK-$i-B" \
      --write-scope 'governance/engineering/**' --dry-run -- true >/tmp/cd-asr-wo2r3-06/race/b.out 2>&1; echo $? > /tmp/cd-asr-wo2r3-06/race/b.rc ) &
  wait
  RA=$(cat /tmp/cd-asr-wo2r3-06/race/a.rc); RB=$(cat /tmp/cd-asr-wo2r3-06/race/b.rc)
  N=0; [ "$RA" -eq 0 ] && N=$((N+1)); [ "$RB" -eq 0 ] && N=$((N+1))
  case $N in 2) DBL=$((DBL+1));; 1) ONE=$((ONE+1));; 0) ZERO=$((ZERO+1));; esac
done
echo "ROUNDS=60  DIFFERENT lease ids, IDENTICAL write_scope='governance/engineering/**'"
echo "  exactly-one-lease (CORRECT)                  : $ONE"
echo "  zero leases                                  : $ZERO"
echo "  *** TWO LEASES ON ONE WRITE SCOPE ***        : $DBL"
