#!/bin/bash

# sean@tanagra.uk
# Fed 2023
#
# This is a wrapper script which will run fioparser 4 times with different IO patterns.
# Courtesy of this article: https://anfcommunity.com/2020/11/20/how-to-nfs-performance-assessment-using-fio-and-fio-parser/
#
# PREREQUISITES
#
# 1.    fio (apt-get fio || yum install fio)
# 2.    fioparser (git clone https://github.com/jtulak/fio-parser.git)
#
# OPTIONS:
#
# --w <working directory>
#       This should point to a directory on whatever volume you're wanting to test. By default it points to /ontap/working,
#       which means it expects you to have a netapp nfs volume mounted to /ontap
#
# --o <output directory>
#       Where you want the results output to
#
# example:
#       ./fioparser.sh -w /zfs/working -o /zfs/output
#
#       In the above example, I am testing an FSX for OpenZFS volume mounted to /zfs
#

# set defaults here
WORKING="/ontap/working"
OUTPUT="/ontap/output"

w=${w:-$WORKING}
o=${o:-$OUTPUT}

while [ $# -gt 0 ]; do
    if [[ $1 == *"--"* ]]; then
        param="${1/--/}"
        declare $param="$2"
    fi
    shift
done

for i in 1 2 3 4 5 6 7 8 9 10 15 20 25 30 40 50 60 70 80 90 100; do 
    fio --name=fiotest --directory=$WORKING --ioengine=libaio --direct=1 --numjobs=2 --nrfiles=4 --runtime=30 --group_reporting --time_based --stonewall --size=4G --ramp_time=20 --bs=64k --rw=read --iodepth=$i --fallocate=none --output=$OUTPUT/$(uname -n)-seqread-$i; 
done

for i in 1 2 3 4 5 6 7 8 9 10 15 20 25 30 40 50 60 70 80 90 100; do 
    fio --name=fiotest --directory=$WORKING --ioengine=libaio --direct=1 --numjobs=2 --nrfiles=4 --runtime=30 --group_reporting --time_based --stonewall --size=4G --ramp_time=20 --bs=64k --rw=write --iodepth=$i --fallocate=none --output=$OUTPUT/$(uname -n)-seqwrite-$i;
done

for i in 1 2 3 4 5 6 7 8 9 10 15 20 25 30 40 50 60 70 80 90 100; do 
    fio --name=fiotest --directory=$WORKING --ioengine=libaio --direct=1 --numjobs=2 --nrfiles=4 --runtime=30 --group_reporting --time_based --stonewall --size=4G --ramp_time=20 --bs=8k --rw=randread --iodepth=$i --fallocate=none --output=$OUTPUT/$(uname -n)-randread-$i;
done

for i in 1 2 3 4 5 6 7 8 9 10 15 20 25 30 40 50 60 70 80 90 100; do
    fio --name=fiotest --directory=$WORKING --ioengine=libaio --direct=1 --numjobs=2 --nrfiles=4 --runtime=30 --group_reporting --time_based --stonewall --size=4G --ramp_time=20 --bs=8k --rw=randwrite --iodepth=$i --fallocate=none --output=$OUTPUT/$(uname -n)-randwrite-$i;
done

/ontap/fio-parser/fio-parser.py -d $OUTPUT
