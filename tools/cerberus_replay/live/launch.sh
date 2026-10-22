#!/bin/bash
SP=${R2_SCRATCH:?set R2_SCRATCH to the directory laid out by fetch_pr14_inputs.sh}
cd $SP
export R2_SCRATCH=$SP R2_TMP=/tmp/r2live_tmp
mkdir -p $R2_TMP
run() { # name repo hist acute
  local name=$1 repo=$2 hist=$3 acute=$4
  for w in 2000-02 2007-09 2011 2015-16 Q4-2018 Mar-2020 2022 Apr-2025; do
    R2_OUT=$SP/live/runs/$name CERBERUS_REPO=$SP/$repo/crash-detector R2_HIST=$hist R2_ACUTE=$acute \
      nice -n 5 python3 -I live/live_replay.py $w > live/runs/$name.$w.log 2>&1 &
  done
}
run A_strict_asis       repo_pr14         none    strict
run B_strict_liveshaped repo_pr14         control strict
run C_avail_liveshaped  repo_pr14_relaxed control available
run D_avail_asis        repo_pr14_relaxed none    available
wait
echo ALLDONE
