#!/usr/bin/python3

"""
sean@tanagra.uk
Aug 2022

arguments:

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --fieldnames [True/False]
        Whether or not to print a header for the CSV (default is False)
    
    -b or --broken [True/False]
        ONLY return instances where SSM isn't able to see the agent at present

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone

prerequisites:

    pip install boto3
    pip install argparse

examples (single region):

    python ec2-instances-in-ssm-by-region.py -f True > mycsv.csv
        Returns list from Virginia with a header and also starts a new CSV (old one will be deleted/overwritten)

    python ec2-instances-in-ssm-by-region.py -r eu-central-1 >> mycsv.csv
        Returns list from Frankfurt with no header (you don't want a header here because its appending to an existing CSV)

example (multiple regions into one CSV):

    python ec2-instances-in-ssm-by-region.py -r eu-west-1 -f True > mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r eu-west-2 >> mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r eu-west-3 >> mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r eu-north-1 >> mycsv.csv

        The example above puts the data for several European regions into one CSV

notes:
    For an instance to be considered working by this script, the following must be ALL true:

    1. AWS Systems Manager Agent (SSM Agent) installed and running within the OS

    2. Instance has connectivity with Systems Manager endpoints
        ! test with these commands:
            Linux:
                nc -vz ssm.<insert region>.amazonaws.com 443
                nc -vz ec2messages.<insert region>.amazonaws.com 443
                nc -vz ssmmessages.<insert region>.amazonaws.com 443

            Powershell:
                Test-NetConnection ssm.<insert region>.amazonaws.com -port 443
                Test-NetConnection ec2messages.<insert region>.amazonaws.com -port 443
                Test-NetConnection ssmmessages.<insert region>.amazonaws.com -port 443

    3. Instance has an appropriate AWS Identity and Access Management (IAM) role attached
        see: https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-profile.html

    4. OS has connectivity to the instance metadata service
        ! test with one of these commands
            Linux:
                curl http://169.254.169.254/latest/meta-data/

            Powershell:
                Invoke-RestMethod -uri http://169.254.169.254/latest/meta-data
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

    parser.add_argument('-b', '--broken',
                        required=False,
                        action='store',
                        help='ONLY show broken SSM agents')

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

    if args.fieldnames:
        fieldnames = args.fieldnames
    else:
        ## change this to True if you want the header to print by default
        fieldnames = False

    if args.broken:
        broken = args.broken
    else:
        ## change this to True if you want to only see broken SSM agents by default
        broken = "False"

    if args.profile:
        profile = str(args.profile)
    else:
        ## change this if you want to change the profile to use
        profile = "default"

    ## boto3 is the main python sdk for AWS
    ## you open connections on a per-service basis
    session = boto3.Session(profile_name=profile)
    ec2 = session.resource('ec2',region_name=region)
    ssm = session.client('ssm',region_name=region)

    ## retrieve ec2 instance data for everything in the target region
    ## see: https://session.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_instance_information
    ec2_data = ec2.instances.all()

    ## retrieve ssm instance data for all EC2 Instances in the target region
    ## see: https://session.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_instance_information
    ssm_data = ssm.describe_instance_information(
        Filters=[
            {
                'Key': 'ResourceType',
                'Values': [
                    'EC2Instance',
                ]
            },
        ]
    )

    ## drop down a level in the JSON
    ssm_instances=ssm_data["InstanceInformationList"]

    if fieldnames == "True":
        ## create header for the CSV but only if the argument -f True was passed
        print(
            "SSM Status" + "," +
            "SSM Computer Name" + "," +
            "SSM Platform" + "," +
            "SSM OS Name" + "," + 
            "SSM Agent" + "," + 
            "SSM Ping" + "," + 
            "SSM IP Address" + "," +
            "EC2 Priv IP" + "," +
            "EC2 Pub IP" + "," +
            "EC2 Instance Id" + "," +            
            "EC2 Instance Type" + "," + 
            "EC2 Avail Zone" + "," +
            "EC2 Instance Profile"
        )

    ## loop over the list retrieved from ec2
    for instance in ec2_data:

        ec2_id = str(instance.id)
        ec2_type = str(instance.instance_type)
        ec2_az = str(instance.placement["AvailabilityZone"])
        ec2_iam = str(instance.iam_instance_profile["Arn"].split("/")[1])
        ec2_ip = str(instance.private_ip_address)
        ec2_pub = str(instance.public_ip_address)
        
        ## first set a marker so we can tell if there is an ec2 instance with no corresponding ssm record at all.  We will count this as broken too.
        no_ssm_hits = True

        ## loop over the list retrieved from ssm
        for ssm_details in ssm_instances:   
            
            ## if this record's ec2 instance id matches the ec2 record's, we know we are talking about the same box
            ## is this idiomatic python?  no, but it keeps us from querying the AWS API more than once (cost savings / rate limit avoidance)

            if (ssm_details["InstanceId"]) == instance.id:
                
                # we found a corresponding record, so don't worry about this anymore
                no_ssm_hits = False

                ssm_computername = str(ssm_details['ComputerName'])
                ssm_platformtype = str(ssm_details['PlatformType'])
                ssm_platformname = str(ssm_details['PlatformName'])
                ssm_ipaddress = str(ssm_details['IPAddress'])
                ssm_agentversion = str(ssm_details['AgentVersion'])
                ssm_pingstatus = str(ssm_details['PingStatus'])
                ssm_broken = "SSM WORKING"

                if (broken == "False"):
                    ## This means they want to see all records, no further thinking required 
                    ssm_showme = True

                elif (broken == "True"):
                    ## This means they set the arg so only broken ones show.  
                    
                    ## The following will detect brokenness
                    if (ssm_pingstatus == "Inactive" or ssm_pingstatus == "Lost Connection"):
                        ssm_showme = True
                        ssm_broken = "SSM BROKEN"
                    else:
                        ssm_showme = False
                else:
                    ## this means they put something odd for the broken argument
                    print("Please put exactly True or False for the --broken argument")
                    return

                if ssm_showme == True:
                    print(
                        ssm_broken + "," +
                        ssm_computername + "," +
                        ssm_platformtype + "," +
                        ssm_platformname + "," +
                        ssm_agentversion + "," + 
                        ssm_pingstatus + "," + 
                        ssm_ipaddress + "," + 
                        ec2_ip + "," +
                        ec2_pub + "," +
                        ec2_id + "," +            
                        ec2_type + "," + 
                        ec2_az + "," + 
                        ec2_iam
                    )
        
        ## this is only if there are no corresponding ssm records
        if no_ssm_hits == True:
            print(
                "SSM BROKEN" + "," +
                "" + "," +
                "" + "," +
                "" + "," +
                "" + "," + 
                "" + "," + 
                "" + "," + 
                ec2_ip + "," +
                ec2_pub + "," +
                ec2_id + "," +            
                ec2_type + "," + 
                ec2_az + "," + 
                ec2_iam
            )

if __name__ == "__main__":
    exit(main())                        
                    
                
                


