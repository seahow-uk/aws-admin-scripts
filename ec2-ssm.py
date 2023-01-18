#!/usr/bin/python3

"""
sean@tanagra.uk
Jan 2023

arguments:
    
    -b or --broken [True/False]
        ONLY return instances where SSM isn't able to see the agent at present

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone

prerequisites:

    pip install boto3
    pip install argparse

examples:

    python3 ec2-ssm.py

        Lists all instances in all regions for the default profile

    python3 ec2-ssm.py --broken True --profile seahow1

        Lists only instances with an SSM status of BROKEN for a profile named "seahow1"

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

    if args.broken:
        broken = args.broken
    else:
        ## change this to True if you want to only see broken SSM agents by default
        broken = "False"

    if args.profile:
        profile = str(args.profile)
    else:
        profile = "noprofile"

    ## Addresses the case where user just wants to use environment variables or default profile
    if (profile == "noprofile"):
        session = boto3.Session()
    else:
        session = boto3.Session(profile_name=profile)   
    
    ec2 = session.client('ec2')
    regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]

    ## Print the header
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

    for region in regions:

        ## see: https://session.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_instance_information
        ec2 = session.resource('ec2',region_name=region)
        ec2_data = ec2.instances.all()

        ## see: https://session.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.describe_instance_information
        ssm = session.client('ssm',region_name=region)
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

        ## loop over the list retrieved from ec2
        for instance in ec2_data:
            
            # stringify instance attributes from boto3 resource
            ec2_id = str(instance.id)
            ec2_type = str(instance.instance_type)
            ec2_ip = str(instance.private_ip_address)
            ec2_pub = str(instance.public_ip_address)

            # As this is a reference which could possibly be of type None, add this logic to prevent an error
            if instance.placement["AvailabilityZone"] is not None:
                ec2_az = str(instance.placement["AvailabilityZone"])
            else:
                ec2_az = "None"

            # As this is a reference which could possibly be of type None, add this logic to prevent an error
            if instance.instance.iam_instance_profile["Arn"] is not None:
                ec2_iam = str(instance.iam_instance_profile["Arn"].split("/")[1])
            else:
                ec2_iam = "None"

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
                    
                
                


