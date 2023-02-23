#!/usr/bin/python3

"""
https://github.com/seahow-uk/aws-admin-scripts
Nov 2022

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --filename [full path the file]
        CSV with the following fields:

        vol-id: the id of the AWS EBS volume you would like to snapshot
        account-id: the AWS account id that the aforementioned volume lives in
        notes: anything you'd like to add as a note which will be appended as a tag to the snapshot

        Be sure to quote the notes field unless its a very simple string

        example of a properly formatted CSV:
        
            vol-9679d0752f6d4177e,751615044823,"This volume was unattached on 2023-01-23 11:01:20 UTC"
            vol-96e69013a141d75c2,751615044823,"This volume is from an old database"
            vol-92f7a074c936739f9,457137834884,"Unknown volume"

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone
    
    -a or --allprofilesallregions [True/False]
        Loop over all configured AWS CLI profiles on this local machine AND pull data from all regions (default is False)
        Note: The script looks for profiles that point to the same account ID and will ignore all duplicates after the first
              This is common when one has a default profile AND an explicit profile pointing to the same account
        
        You do not need to specify the region or profile if you use this option

prerequisites:

    pip3 install boto3
    pip3 install argparse
    pip3 install csv

examples:

    Running against a specific region with the default profile

        python3 ebs-snapshot-to-archive.py -r eu-west-1 -f ./myebsvolumes.csv
    
    Running against all regions and all accounts configured in your local AWS CLI

        python3 ebs-snapshot-to-archive.py -a True -f ./myebsvolumes.csv

"""

import boto3
import argparse
import sys
import csv

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

    parser.add_argument('-a', '--allprofilesallregions',
                        required=False,
                        action='store',
                        help='If you want to loop over all local profiles and pull from all regions')

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

    if args.allprofilesallregions:
        allprofilesallregions = args.allprofilesallregions
    else:
        allprofilesallregions = False

    ## Addresses the case where user just wants to use environment variables or default profile
    if (profile == "noprofile"):
        session = boto3.Session()
    else:
        session = boto3.Session(profile_name=profile)

    ## If profile is set to "all", get a list of available local profiles on this box
    if allprofilesallregions == "True" or allprofilesallregions == "true":
        profile_list = boto3.session.Session().available_profiles
    else:
        # if we're not doing that, we'll just have a single entry list
        profile_list = profile.split()
   
    file = open(filename, "r")
    csvReader = csv.reader( file,  delimiter=",", quotechar='"')

    # set up empty data structures to track account ids and errors
    profile_dict = {}
    csv_account_id_list = []

    # get the unique account ids from the CSV
    for row in csvReader:
        if (row[1] not in csv_account_id_list):
            csv_account_id_list.append(row[1])

    # get the unique account ids from the local profiles, i.e. what they actually have access to
    for this_profile in profile_list:
        print("profile:" + this_profile)
        # Open a session and get the info for list particular profile
        # UNLESS they didn't specify a profile at all in which case just use env vars or whatever they're doing
        if this_profile == "noprofile":
            session = boto3.Session()
        else:
            session = boto3.Session(profile_name=this_profile)

        try:
            STS_CLIENT = session.client('sts')
            CURRENT_ACCOUNT_ID = STS_CLIENT.get_caller_identity()['Account']
            
            if CURRENT_ACCOUNT_ID not in profile_dict:
                profile_dict[CURRENT_ACCOUNT_ID] = this_profile

        except:
            print("ERROR: cannot get the current Account ID from the STS service for profile " + this_profile + ".  This can be caused by a profile meant for a snow family device or insufficient permissions")
            sys.exit()

    # validate that they do, in fact, have a local profile with credentials for every account id in their CSV
    for this_account in csv_account_id_list:
        if (this_account not in profile_dict):
            print("ERROR: account " + this_account + " which is listed in your CSV does not have a matching local profile/credentials in your AWS CLI configuration")
            sys.exit()

    print(profile_dict)

    # ## loop through each volume and retrieve its snapshots
    # for line in Lines:
    #     count += 1
    #     volume_id_list.append(line.strip())
    
    # volume_list_file.close()

    # print ("number of volumes we need to snapshot:" + str(len(volume_id_list)))

    # volume_id_list = []
    # snapshot_id_list = []
    # ec2client = session.client('ec2',region_name=region)
    # ec2resource = session.resource('ec2',region_name=region)
    # count = 0
    # for vol in volume_id_list:
    #     count += 1
    #     snapname = ("Archival Snapshot of " + vol)
    #     ## we need to use ec2resource here because it has the ability to wait
    #     snapshot = ec2resource.create_snapshot(
    #         VolumeId=vol,
    #         TagSpecifications=[
    #             {
    #                 'ResourceType': 'snapshot',
    #                 'Tags': [
    #                     {
    #                         'Key': 'Name',
    #                         'Value': snapname
    #                     },
    #                 ]
    #             },
    #         ]
    #     )
    #     print ("creating snapshot for volume: " + vol)
    #     snapshot.wait_until_completed()
    #     print ("snapshot " + snapshot.snapshot_id + " complete.")
    #     snapshot_id_list.append(snapshot.snapshot_id)

    # count = 0
    # for snap in snapshot_id_list:
    #     count += 1
    #     ## we need to use ec2client here because it has the ability to modify the snapshot tier
    #     snapshot = ec2client.modify_snapshot_tier(
    #         SnapshotId=snap,
    #         StorageTier='archive'
    #     )
    #     print ("initiating archive of snapshot: " + snap)

    # print ("Note: the snapshots are still being tiered down to archive.  How long this takes can vary a lot.")
    # print ("Double check the tiering status in the console under EC2 > Snapshots > [snapshot] > Storage Tier tab")

if __name__ == "__main__":
    exit(main())                        
                    
                
                


