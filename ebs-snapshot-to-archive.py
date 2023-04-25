#!/usr/bin/python3

"""

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --filename [full path the file]
        CSV with the following fields:

        vol-id: the id of the AWS EBS volume you would like to snapshot
        account-id: the AWS account id that the aforementioned volume lives in
        region: the AWS region name that the volume lives in
        notes: anything you'd like to add as a note which will be appended as a tag to the snapshot

        Be sure to quote the notes field unless its a very simple string

        example of a properly formatted CSV:
        
            vol-9679d0752f6d4177e,751615044823,us-east-1,"Notes for my favorite volume"
            vol-96e69013a141d75c2,751615044823,eu-west-1,"This volume is from an old database"
            vol-92f7a074c936739f9,457137834884,us-east-1,"Unknown volume"

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
from datetime import datetime

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
    csvReader = csv.reader( file,  delimiter=",", quotechar="'")

    # set up empty data structures to track stuff
    profile_dict = {}
    csv_account_id_list = []
    error_list = []
    volume_dict = {}
    csv_region_list = []
    snapshot_dict = {}
    archived_dict = {}

    # set up constants
    utc_date_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    date_format_str = '%Y-%m-%d %H:%M:%S'

    # get info out of the CSV
    for row in csvReader:

        if (row[1] not in csv_account_id_list):
            csv_account_id_list.append(row[1])
        
        if (row[0] not in volume_dict):
            
            new_volume = row[0]
            new_account = row[1]
            new_region = row[2]
            new_notes = row[3]

            volume_dict[new_volume] = [new_account, new_region, new_notes]
        
        if (row[2] not in csv_region_list):
            csv_region_list.append(row[2])

    # in the special case that they are specifying one region we will just create a single region list here    
    if allprofilesallregions == "False":
        csv_region_list = [region]

    # get the unique account ids from the local profiles, i.e. what they actually have access to
    for this_profile in profile_list:

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
            error_list.append("ERROR: cannot get the current Account ID from the STS service for profile " + this_profile + ".  This can be caused by a profile meant for a snow family device or insufficient permissions")

    # validate that they do, in fact, have a local profile with credentials for every account id in their CSV
    for this_account in csv_account_id_list:
        if (this_account not in profile_dict):
            error_list.append("ERROR: account " + this_account + " which is listed in your CSV does not have a matching local profile/credentials in your AWS CLI configuration")

    # loop over each profile again, this time from the known good dictionary
    for this_account,this_profile in profile_dict.items():

        this_session = boto3.Session(profile_name=this_profile)

        # ok, so let's loop over the csv_region_list which should be much narrower than all possible regions
        for this_region in csv_region_list:

            # open an ec2 resource and ec2 client for this specific profile and region within it
            this_ec2_resource = this_session.resource('ec2',region_name=this_region)
            this_ec2_client = this_session.client('ec2',region_name=this_region)

            # loop over the volume_dict and only snapshot ones in this account and region
            # remember volume_dict looks like this
            # volume_id : ['account_id', 'region', 'notes'] 

            for this_volumes_id,this_volumes_list in volume_dict.items():
                
                this_volumes_id = str(this_volumes_id)

                this_volumes_account = this_volumes_list[0]
                this_volumes_region = this_volumes_list[1]
                this_volumes_notes = this_volumes_list[2]
                # first off, only bother with volumes tied to the account we're in
                if this_volumes_account == this_account:

                    # now, only bother if the volume is in the region we're in
                    if this_volumes_region == this_region:
                        print("creating snapshot for: ",this_volumes_id,this_volumes_account,this_volumes_region,this_volumes_notes + "...(waiting)...")

                        # by default we'll assume a volume has no name
                        this_volume_name = "unnamed"

                        try:
                            this_volumes_data = this_ec2_resource.Volume(this_volumes_id)
                        except:
                            error_list.append("ERROR: Something is wrong with " + this_volumes_id + " it might be a nonexistent vol-id?")
                        try:
                            if this_volumes_data.tags:
                                for t in this_volumes_data.tags:
                                    if t["Key"] == 'Name':
                                        this_volume_name = t["Value"]  
                        except:
                            error_list.append("ERROR: Something is wrong with " + this_volumes_id + " it might be a nonexistent vol-id?")

                        try:
                            this_volume_type = str(this_volumes_data.volume_type)
                            this_volume_az = str(this_volumes_data.availability_zone)
                            this_volume_size = str(this_volumes_data.size)
                            this_volume_encrypted = str(this_volumes_data.encrypted)
                            this_volume_created = str(this_volumes_data.create_time.strftime(date_format_str))
                        except:
                            error_list.append("ERROR: Something is wrong with " + this_volumes_id + " it might be a nonexistent vol-id?")


                        snapshot_name = ("archive of " + this_volume_name + " created " + utc_date_time)

                        try:
                            this_snapshot = this_ec2_resource.create_snapshot(
                                VolumeId=this_volumes_id,
                                TagSpecifications=[
                                    {
                                        'ResourceType': 'snapshot',
                                        'Tags': [
                                            {
                                                'Key': 'Name',
                                                'Value': snapshot_name
                                            },
                                            {
                                                'Key': 'Volume Name',
                                                'Value': this_volume_name
                                            },                                            
                                            {
                                                'Key': 'Volume Type',
                                                'Value': this_volume_type
                                            },
                                            {
                                                'Key': 'Volume AZ',
                                                'Value': this_volume_az
                                            },
                                            {
                                                'Key': 'Volume Size',
                                                'Value': this_volume_size
                                            },
                                            {
                                                'Key': 'Volume Encrypted',
                                                'Value': this_volume_encrypted
                                            },
                                            {
                                                'Key': 'Volume Created',
                                                'Value': this_volume_created
                                            },
                                            {
                                                'Key': 'Notes',
                                                'Value': this_volumes_notes
                                            },
                                        ]
                                    },
                                ]
                            )
                            this_snapshot.wait_until_completed()
                            print ("snapshot " + this_snapshot.snapshot_id + " complete.")
                            # this is where we will store information about snapshots that were successful
                            snapshot_dict[this_snapshot.snapshot_id] = [this_volumes_id, this_volumes_account, this_volumes_region, this_volumes_notes]

                        except:
                            error_list.append("ERROR: Initial snapshot of volume " + this_volumes_id + " failed")

            # loop over snapshots in this account and region to try and tier them down to archive
            for this_snapshots_id,this_snapshots_list in snapshot_dict.items():

                this_snapshots_volume_id = this_snapshots_list[0]
                this_snapshots_account = this_snapshots_list[1]
                this_snapshots_region = this_snapshots_list[2]
                this_snapshots_notes = this_snapshots_list[3]
                
                try:
                    this_ec2_client.modify_snapshot_tier(
                        SnapshotId=this_snapshots_id,
                        StorageTier='archive'
                    )
                    print ("initiating archive of: ",this_snapshots_id,this_snapshots_volume_id,this_snapshots_account,this_snapshots_region,this_snapshots_notes)
                    archived_dict[this_snapshots_id] = [this_snapshots_id,this_snapshots_volume_id,this_snapshots_account,this_snapshots_region,this_snapshots_notes]
                except:
                    error_list.append("ERROR: Archival of snapshot " + this_snapshots_id + " failed")

    print ("Note: the snapshots are still being tiered down to archive.  How long this takes can vary a lot.")
    print ("Double check the tiering status in the console under EC2 > Snapshots > [snapshot] > Storage Tier tab")

    print (" ")
    print (error_list)
    # write the output to a file for troubleshooting

    archive_file = 'archived_snapshots_output.csv'

    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write("")

    for this_snapshots_id,this_snapshots_list in archived_dict.items():
        with open(archive_file,'a',encoding='utf-8') as f:
            f.write( f"{this_snapshots_list}\n")

if __name__ == "__main__":
    exit(main())                        
                    
                
                


