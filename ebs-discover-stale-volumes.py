#!/usr/bin/python3

"""
sean@tanagra.uk
Nov 2022

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --fieldnames [True/False]
        Whether or not to print a header for the CSV (default is False)

prerequisites:

    pip install boto3
    pip install argparse

examples (single region):

    python ebs-discover-stale-volumes.py -f True > mycsv.csv
        Returns list from Virginia with a header and also starts a new CSV (old one will be deleted/overwritten)

    python ebs-discover-stale-volumes.py -r eu-central-1 >> mycsv.csv
        Returns list from Frankfurt with no header (you don't want a header here because its appending to an existing CSV)

example (multiple regions into one CSV):

    python ebs-discover-stale-volumes.py -r eu-west-1 -f True > mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-west-2 >> mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-west-3 >> mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-north-1 >> mycsv.csv

        The example above puts the data for several European regions into one CSV

"""

import boto3
import argparse, time, os, json
from datetime import datetime
from datetime import timedelta

STS_CLIENT = boto3.client('sts')
CURRENT_ACCOUNT_ID = STS_CLIENT.get_caller_identity()['Account']

def setup_args():
    parser = argparse.ArgumentParser(
        description='Optional arguments')

    parser.add_argument('-r', '--region',
                        required=False,
                        action='store',
                        help='AWS region to retrieve data from')

    parser.add_argument('-f', '--fieldnames',
                        required=False,
                        action='store',
                        help='Whether to include a CSV header')

    return (parser.parse_args())

def main():
    args = setup_args()

    if args.region:
        region = str(args.region)
    else:
        ## change this if you want to change the region it defaults to
        region = "us-east-1"

    if args.fieldnames:
        fieldnames = args.fieldnames
    else:
        ## change this to True if you want the header to print by default
        fieldnames = False

    ## boto3 is the main python sdk for AWS
    ## you open connections on a per-service basis
    ec2 = boto3.resource('ec2',region_name=region)

    ## retrieve all ebs volume info in the target region
    vol_data = ec2.volumes.all()

    ## retrieve all snapshots owned by this account in this region, excluding the many public ones
    snap_data = ec2.snapshots.filter(
        OwnerIds=[
            CURRENT_ACCOUNT_ID
        ]
    )
    
    ## set up how we want our dates formatted
    date_format_str = '%B %Y'

    if fieldnames == "True" or fieldnames == "true":
        ## create header for the CSV but only if the argument -f True was passed
        print(
            "Vol ID" + "," +
            "Vol Name" + "," +
            "Avail Zone" + "," +
            "Vol Type" + "," +
            "Encrypted" + "," +
            "GB Size" + "," +
            "Created" + "," +            
            "Snaps in Archive" + "," +
            "Most Recent Snap in Archive"
        )

    ## loop over the list retrieved from ec2
    for volume in vol_data:

        vol_name = "unnamed"

        if volume.tags:
            for t in volume.tags:
                if t["Key"] == 'Name':
                    vol_name = t["Value"]  

        vol_id = str(volume.id)
        vol_type = str(volume.volume_type)
        vol_az = str(volume.availability_zone)
        vol_size = str(volume.size)
        vol_state = str(volume.state)
        vol_encrypted = str(volume.encrypted)
        vol_created = str(volume.create_time.strftime(date_format_str))
        

        snaps_in_volume=0
        snaps_in_volume_list=[]
        for snap in snap_data:
            if snap.volume_id == vol_id and snap.storage_tier == 'archive':
                snaps_in_volume=snaps_in_volume+1
                snaps_in_volume_list.append(snap.start_time)

        most_recent_snap_date = 'none'

        if snaps_in_volume > 0:
            most_recent_snap_date = max(snaps_in_volume_list).strftime(date_format_str)

        vol_archived = most_recent_snap_date

        if (vol_state) == "available":

            print(
                vol_id + "," +
                vol_name + "," +
                vol_az + "," + 
                vol_type + "," +
                vol_encrypted + "," +
                vol_size + "," + 
                vol_created + "," + 
                str(snaps_in_volume) + "," +
                vol_archived
            )

def date_compare(snap1, snap2):
    if snap1.start_time < snap2.start_time:
        return 1
    elif snap1.start_time == snap2.start_time:
        return 0
    return -1

if __name__ == "__main__":
    exit(main())                        
                    
                
                


