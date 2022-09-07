#!/usr/bin/python3

"""
sean@tanagra.uk
Aug 2022

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --fieldnames [True/False]
        Whether or not to print a header for the CSV (default is False)

prerequisites:

    pip install boto3
    pip install argparse

examples:

    rds-maintenance-windows.py -r us-east-1 -f True > mycsv.csv
    rds-maintenance-windows.py -r ap-northeast-1 >> mycsv.csv
    rds-maintenance-windows.py -r ap-southeast-2 >> mycsv.csv

    The above will create a csv that covers 3 regions around the world

"""

import boto3
import argparse
from datetime import datetime
from datetime import timedelta

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
    
    ## set up the timezone-to-region mapping
    region_utc_offset_no_dst = {
        "us-gov-west-1" : "-8",
        "us-west-1" : "-8",
        "us-west-2" : "-8",
        "ca-west-1" : "-6",
        "ca-central-1" : "-5",
        "us-east-1" : "-5",
        "us-east-2" : "-5",
        "us-gov-east-1" : "-5",
        "sa-east-1" : "-3",
        "eu-west-1" : "0",
        "eu-west-2" : "0",
        "eu-central-2" : "1",
        "eu-north-1" : "1",
        "eu-west-3" : "1",
        "af-south-1" : "2",
        "eu-central-1" : "2",
        "eu-east-1" : "2",
        "eu-south-1" : "2",
        "me-west-1" : "2",
        "me-south-1" : "3",
        "me-south-2" : "4",
        "ap-south-1" : "5.5",
        "ap-south-2" : "5.5",
        "ap-southeast-3" : "7",
        "ap-east-1" : "8",
        "ap-southeast-1" : "8",
        "cn-north-1" : "8",
        "cn-northwest-1" : "8",
        "ap-northeast-1" : "9",
        "ap-northeast-2" : "9",
        "ap-northeast-3" : "9",
        "ap-southeast-2" : "10",
        "ap-southeast-4" : "12"
    }

    ## boto3 is the main python sdk for AWS
    ## you open connections on a per-service basis
    rds = boto3.client('rds',region_name=region)

    rds_data = rds.describe_db_instances()

    if fieldnames == "True":
        ## create header for the CSV but only if the argument -f True was passed
        print(
            "RDS Instance" + "," +
            "Instance Type" + "," +
            "DB Engine" + "," + 
            "Version" + "," + 
            "Status" + "," + 
            "Avail Zone" + "," +
            "Minor Ver Upg" + "," +
            "MW UTC Day" + "," +
            "MW UTC Start" + "," +
            "MW UTC End"  + "," +
            "MW Local Start" + "," +
            "MW Local End"
        )

    for instance in rds_data['DBInstances']:
        rds_instance_DBInstanceIdentifier = str(instance['DBInstanceIdentifier'])
        rds_instance_DBInstanceClass = str(instance['DBInstanceClass'])
        rds_instance_Engine = str(instance['Engine'])
        rds_instance_EngineVersion = str(instance['EngineVersion'])
        rds_instance_DBInstanceStatus = str(instance['DBInstanceStatus'])
        rds_instance_AvailabilityZone = str(instance['AvailabilityZone'])
        rds_instance_AutoMinorVersionUpgrade = str(instance['AutoMinorVersionUpgrade'])

        ## convert to the time zone the region is actually in
        rds_instance_PreferredMaintenanceWindow_UTC = str(instance['PreferredMaintenanceWindow'])
        rds_instance_PreferredMaintenanceWindow_UTC_day_start = rds_instance_PreferredMaintenanceWindow_UTC[0:3]
        # rds_instance_PreferredMaintenanceWindow_UTC_day_end = rds_instance_PreferredMaintenanceWindow_UTC[10:13]
        rds_instance_PreferredMaintenanceWindow_UTC_time_start = rds_instance_PreferredMaintenanceWindow_UTC[4:9]
        rds_instance_PreferredMaintenanceWindow_UTC_time_end = rds_instance_PreferredMaintenanceWindow_UTC[14:19]

        # this yields the region name
        rds_instance_region = rds_instance_AvailabilityZone[0:(len(rds_instance_AvailabilityZone)-1)]
        
        # this gives the region's UTC offset
        rds_instance_region_utc_offset = region_utc_offset_no_dst[rds_instance_region]

        # format string
        date_format_str = '%H:%M'

        # This figures out the local times from the region's timezone
        # NOTE: this does not take daylight savings into account

        rds_instance_PreferredMaintenanceWindow_UTC_time_start_timeformatted = datetime.strptime(rds_instance_PreferredMaintenanceWindow_UTC_time_start, date_format_str)      
        rds_instance_PreferredMaintenanceWindow_local_time_start_timeformatted = rds_instance_PreferredMaintenanceWindow_UTC_time_start_timeformatted + timedelta(hours=float(rds_instance_region_utc_offset))
        rds_instance_PreferredMaintenanceWindow_local_time_start = rds_instance_PreferredMaintenanceWindow_local_time_start_timeformatted.strftime('%H:%M')
        
        rds_instance_PreferredMaintenanceWindow_UTC_time_end_timeformatted = datetime.strptime(rds_instance_PreferredMaintenanceWindow_UTC_time_end, date_format_str)      
        rds_instance_PreferredMaintenanceWindow_local_time_end_timeformatted = rds_instance_PreferredMaintenanceWindow_UTC_time_end_timeformatted + timedelta(hours=float(rds_instance_region_utc_offset))
        rds_instance_PreferredMaintenanceWindow_local_time_end = rds_instance_PreferredMaintenanceWindow_local_time_end_timeformatted.strftime('%H:%M')


        print(
            rds_instance_DBInstanceIdentifier + "," +
            rds_instance_DBInstanceClass + "," +
            rds_instance_Engine + "," +
            rds_instance_EngineVersion + "," +
            rds_instance_DBInstanceStatus + "," +
            rds_instance_AvailabilityZone + "," +
            rds_instance_AutoMinorVersionUpgrade + "," +
            rds_instance_PreferredMaintenanceWindow_UTC_day_start + "," +
            rds_instance_PreferredMaintenanceWindow_UTC_time_start + "," +
            rds_instance_PreferredMaintenanceWindow_UTC_time_end  + "," +
            rds_instance_PreferredMaintenanceWindow_local_time_start + "," +
            rds_instance_PreferredMaintenanceWindow_local_time_end         
        )

if __name__ == "__main__":
    exit(main())                        
                    
                
                


