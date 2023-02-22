#!/usr/bin/python3

"""
https://github.com/seahow-uk/aws-admin-scripts
Nov 2022

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --filename [full path the file]
        file that is a list of ebs volume-ids you want to snapshot to archive

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone

prerequisites:

    pip install boto3
    pip install argparse

example:

    python ebs-snapshot-to-archive.py -r eu-west-1 -f ./myebsvolumes.txt

"""

import boto3
import argparse
import sys



def setup_args():
    parser = argparse.ArgumentParser(
        description='Optional arguments')

    parser.add_argument('-r', '--region',
                        required=False,
                        action='store',
                        help='AWS region to retrieve data from')

    parser.add_argument('-f', '--filename',
                        required=True,
                        action='store',
                        help='Full or relative path to a file with a list of volume-ids')

    parser.add_argument('-p', '--profile',
                        required=False,
                        action='store',
                        help='If you want to use a non-default profile')

    return (parser.parse_args())

def main():
    args = setup_args()

    if args.region:
        region = str(args.region)
    else:
        ## change this if you want to change the region it defaults to
        region = "us-east-1"

    if args.filename:
        filename = args.filename
    else:
        sys.exit("Filename somehow didn't make it through the argument")

    if args.profile:
        profile = str(args.profile)
    else:
        profile = "noprofile"

    ## Addresses the case where user just wants to use environment variables or default profile
    if (profile == "noprofile"):
        session = boto3.Session()
    else:
        session = boto3.Session(profile_name=profile)   

    # Using readlines() to get the ebs volume-id list
    volume_list_file = open(filename, "r")
    Lines = volume_list_file.readlines()
    count = 0

    ec2client = session.client('ec2',region_name=region)
    ec2resource = session.resource('ec2',region_name=region)
    
    volume_id_list = []
    snapshot_id_list = []

    ## loop through each volume and retrieve its snapshots
    for line in Lines:
        count += 1
        volume_id_list.append(line.strip())
    
    volume_list_file.close()

    print ("number of volumes we need to snapshot:" + str(len(volume_id_list)))

    count = 0
    for vol in volume_id_list:
        count += 1
        snapname = ("Archival Snapshot of " + vol)
        ## we need to use ec2resource here because it has the ability to wait
        snapshot = ec2resource.create_snapshot(
            VolumeId=vol,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': snapname
                        },
                    ]
                },
            ]
        )
        print ("creating snapshot for volume: " + vol)
        snapshot.wait_until_completed()
        print ("snapshot " + snapshot.snapshot_id + " complete.")
        snapshot_id_list.append(snapshot.snapshot_id)

    count = 0
    for snap in snapshot_id_list:
        count += 1
        ## we need to use ec2client here because it has the ability to modify the snapshot tier
        snapshot = ec2client.modify_snapshot_tier(
            SnapshotId=snap,
            StorageTier='archive'
        )
        print ("initiating archive of snapshot: " + snap)

    print ("Note: the snapshots are still being tiered down to archive.  How long this takes can vary a lot.")
    print ("Double check the tiering status in the console under EC2 > Snapshots > [snapshot] > Storage Tier tab")

if __name__ == "__main__":
    exit(main())                        
                    
                
                


