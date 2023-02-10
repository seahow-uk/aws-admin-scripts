#!/usr/bin/python3

"""
sean@tanagra.uk
Nov 2022

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --fieldnames [True/False]
        Whether or not to print a header for the CSV (default is True)

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone
    
    -a or --allprofilesallregions [True/False]
        Loop over all configured AWS CLI profiles on this local machine AND pull data from all regions (default is False)

prerequisites:

    pip install boto3
    pip install argparse

example 1 (single region):

    python ebs-discover-stale-volumes.py -f True > mycsv.csv
        Returns list from Virginia with a header and also starts a new CSV (old one will be deleted/overwritten)

    python ebs-discover-stale-volumes.py -r eu-central-1 >> mycsv.csv
        Returns list from Frankfurt with no header (you don't want a header here because its appending to an existing CSV)

example 2 (multiple regions into one CSV):

    python ebs-discover-stale-volumes.py -r eu-west-1 -f True > mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-west-2 >> mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-west-3 >> mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-north-1 >> mycsv.csv

        The example above puts the data for several European regions into one CSV

example 3 (all profiles all regions)

    python ebs-discover-stale-volumes.py -a True

        The example above loops over all local AWS CLI profiles configured on this box AND pulls data from all regions
        Note: This can take a long time to run if you have more than a couple profiles

"""

import boto3
import argparse

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

    if args.fieldnames:
        fieldnames = args.fieldnames
    else:
        fieldnames = True

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
        region_list = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
    else:
        # I realize this is clunky, this is something I'm adding onsite for a specific last minute request
        profile_list = profile.split()
        region_list = region.split()

    for this_profile in profile_list:
        # Open a session and get the info for list particular profile
        session = boto3.Session(profile_name=this_profile)
        STS_CLIENT = session.client('sts')
        CURRENT_ACCOUNT_ID = STS_CLIENT.get_caller_identity()['Account']

        # Loop over the region_list, which is either a single specified region or all of them
        for this_region in region_list:
            ## boto3 is the main python sdk for AWS
            ## you open connections on a per-service basis
            ec2 = session.resource('ec2',region_name=this_region)

            ## retrieve all ebs volume info in the target region
            vol_data = ec2.volumes.filter(
                Filters=[
                    {
                        'Name': 'status',
                        'Values': [
                            'available',
                        ]           
                    }
                ]
            )

            ## retrieve all snapshots owned by this account in this region, excluding the many public ones
            snap_data = ec2.snapshots.filter(
                Filters=[
                    {
                        'Name': 'status',
                        'Values': [
                            'completed',
                        ],
                        'Name': 'owner-id',
                        'Values': [
                            CURRENT_ACCOUNT_ID,
                        ],
                        'Name': 'storage-tier',
                        'Values': [
                            'archive',
                        ]
                    }
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
                    if snap.volume_id == vol_id:
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

if __name__ == "__main__":
    exit(main())                        
                    
                
                


