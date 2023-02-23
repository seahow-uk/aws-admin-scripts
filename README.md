# **aws-admin-scripts**

Misc infrastructure management utilities for use with the AWS platform

Meant to serve as examples/starting points for further customization.  No warranty express or implied.  

[**[rds-maintenance-windows]**](#rds-maintenance-windowspy)&nbsp;&nbsp;&nbsp; [**[admin-instance]**](#admin-instanceyaml)&nbsp;&nbsp;&nbsp; [**[al2-desktop-installer]**](#al2-desktop-installersh)&nbsp;&nbsp;&nbsp; [**[ec2-ssm]**](#ec2-ssmpy)&nbsp;&nbsp;&nbsp; 

[**[ebs-discover-stale-volumes]**](#ebs-discover-stale-volumespy)&nbsp;&nbsp;&nbsp; [**[ebs-snapshot-to-archive]**](#ebs-snapshot-to-archivepy)&nbsp;&nbsp;&nbsp; [**[fioparser]**](#fioparsersh)&nbsp;&nbsp;&nbsp; [**[sso-auth]**](#sso-authpy)&nbsp;&nbsp;&nbsp; 
## **admin-instance.yaml**
[**[Back to Top]**](#aws-admin-scripts)

CloudFormation template that will spin up an Amazon Linux 2 instance with SSM and CloudWatch agents + everything needed to run these scripts.  It also creates a log group in CloudWatch and streams important logs to it.  Further, the al2-desktop-installer.sh script mentioned below will be run as part of the setup.  Refer to that section for details.

**NOTE:** This repo gets cloned to /opt/aws/aws-admin-scripts .  As root, you should be able to cd to that directory and start executing scripts.

![image](https://user-images.githubusercontent.com/112027478/206909795-ffd9e330-9d51-4692-b30e-25559229ff63.png)

**Required parameters:**

    KeyPair - Select an EC2 KeyPair in that region

    Subnet - Select a Subnet in the VPC you would like to deploy this instance to

    SecurityGroup - Select a Security Group you would like to attach to this instance

    InstanceProfile - An IAM Role that has permissions to send messages to EC2, 
                      post CloudWatch Metrics, and communicate with SSM

    Note: Also included in this repo is a file called admin-instance-role-policy.json.  
    This is an example policy which can be used to create an IAM Role with appropriate permissions.

**Optional parameters:**

    InstanceType - Select one of the instance types from the dropdown.  
    Default is t3a.micro.

    LinuxAMI - You should leave this at the default unless you know what you're doing. 
    This is pulling the latest AMI ID from a public SSM parameter.

    PVSize - This instance will get a secondary EBS volume mounted on /data this size.  
    Default is 36.

    PVType - The aforementioned EBS volume will be of the type you select here.  
    Default is GP3.

    TimeZone - Select one of the TimeZones here.  
    Note: I need to expand this list.

## **al2-desktop-installer.sh**
[**[Back to Top]**](#aws-admin-scripts)

installs and configures MATE + VNC (plus all desktop utilities) for an EC2 instance running Amazon Linux 2 (will fail on other distros)

![image](https://user-images.githubusercontent.com/112027478/204065554-7a3b5585-87b0-4562-8c7a-c28dd8ca0ab0.png)

**Optional parameters:**

    --p <password> 
        VNC password will be set to AWS@todaysdate (in this format: AWS@yyyymmdd) unless you specify your own
        for instance, were I to not supply a password and run the script on Nov 26, 2022 it would
        set the VNC login password to "AWS@20221126".  This is obviously insecure and meant for labs only

    --r <runasuser>
        VNC will run as root unless you tell it a different user to run as 

    example:
        ./al2-desktop-installer.sh --p 0neD1rect10nRulez2001 --r someuser

## **ec2-ssm.py**
[**[Back to Top]**](#aws-admin-scripts)

A report that merges information from SSM with EC2 data to help diagnose when SSM is broken for one or more
EC2 instances.

**Optional parameters:**

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        only use this if you want to limit it to a single profile/account
    
    -a or --allprofilesallregions [True/False]
        Loop over all configured AWS CLI profiles on this local machine AND pull data from all regions (default is False)
        Note: The script looks for profiles that point to the same account ID and will ignore all duplicates after the first
              This is common when one has a default profile AND an explicit profile pointing to the same account

![image](https://user-images.githubusercontent.com/112027478/220175799-dd45c0fe-d030-49de-ad1f-0452e01a4c72.png)

**To produce the above example (all profiles and all regions):**	

    python3 ./ec2-ssm.py -a True

## **rds-maintenance-windows.py**
[**[Back to Top]**](#aws-admin-scripts)

Figure out what the maintenance windows are set to across deployed rds instances in both UTC and local time

![image](https://user-images.githubusercontent.com/112027478/188876917-8c506f5a-a271-4dd0-928e-fe5c96e2d758.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python3 ec2-instances-in-ssm-by-region.py -r us-east-1 -f True > mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r ap-southeast-1 >> mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r ap-northeast-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

## **ebs-discover-stale-volumes.py**
[**[Back to Top]**](#aws-admin-scripts)

Pulls a list of all volumes that are currently unattached and gives you their details, including whether or not it has at least one snapshot in the Archive tier.  If there is more than one snapshot in the Archive tier, it will show the most recent one’s date.

**Optional parameters:**

    -r or --region [String]
        AWS region to use (default is us-east-1)

    -f or --fieldnames [True/False]
        Whether or not to print a header for the CSV (default is True)

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone
    
    -a or --allprofilesallregions [True/False]
        Loop over all configured AWS CLI profiles on this local machine AND pull data from all regions (default is False)
        Note: The script looks for profiles that point to the same account ID and will ignore all duplicates after the first
              This is common when one has a default profile AND an explicit profile pointing to the same account

![image](https://user-images.githubusercontent.com/112027478/218100475-249eb3ac-8d30-4ca5-b3ab-1258d31d843c.png)

**To produce the above example (all profiles and all regions):**

    python3 ebs-discover-stale-volumes.py -a True

        - This option will make it loop over all profiles explicitly configured in your local AWS CLI client (~/.aws/credentials)
        - Within each profile, it will loop over all regions that account can see (meaning this could vary if some accounts 
          have optional regions enabled)
        - If it encounters a problem with a given profile (such as insufficient permissions), it continues on and gives an 
          error at the end of the output
        - It will ignore repeats of the same Account ID.  So if you have a default profile then an explicitly named profile 
          pointing to the same account it only gets the first one

![ebs-snaps](https://user-images.githubusercontent.com/112027478/201394313-691ff847-9636-4598-bd5e-97ba5c0d0a16.png)

**To produce the above example (specific regions rolled into one CSV):**

    python3 ebs-discover-stale-volumes.py -r eu-west-1 > mycsv.csv
    python3 ebs-discover-stale-volumes.py -r eu-west-2 -f False >> mycsv.csv
    python3 ebs-discover-stale-volumes.py -r eu-west-3 -f False >> mycsv.csv
    python3 ebs-discover-stale-volumes.py -r eu-north-1 -f False >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the all but the first one has the "-f False" parameter set, to avoid duplicating headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

## **ebs-snapshot-to-archive.py**
[**[Back to Top]**](#aws-admin-scripts)

given a list of volume-ids in a file (one per line, no other characters), this will snapshot the volumes in question, wait for that to finish, then move the snapshots to the archive tier.  The idea here is you want to take one last snapshot for the record before deleting a list.

**Prerequisites**

    pip3 install boto3
    pip3 install argparse
    pip3 install csv

**Optional parameters:**

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
        
            vol-9679d0752f6d4177e,751615044823,us-east-1,"This volume was unattached on 2023-01-23 11:01:20 UTC"
            vol-96e69013a141d75c2,751615044823,eu-west-1,"This volume is from an old database"
            vol-92f7a074c936739f9,457137834884,us-east-1,"Unknown volume"

    -p or --profile [String]
        Specify the AWS client profile to use - found under ~/.aws/credentials
        If you don't have multiple profiles, leave this alone
    
    -a or --allprofilesallregions [True/False]
        Loop over all configured AWS CLI profiles on this local machine and hit all regions in the CSV
        
        You do not need to specify the region with -r or a profile with -p if you use this option

![image](https://user-images.githubusercontent.com/112027478/221023030-4659a9ba-5a15-4621-8f7a-aca8414f9d76.png)

**To produce the above example:**

    python3 ebs-snapshot-to-archive.py -a True -f ./testvol.csv 

## **fioparser.sh**
[**[Back to Top]**](#aws-admin-scripts)

This is a wrapper script which will run fioparser 4 times with different IO patterns.
Courtesy of this article: https://anfcommunity.com/2020/11/20/how-to-nfs-performance-assessment-using-fio-and-fio-parser/

**Prerequisites**

    1.    fio (apt install fio || yum install fio)
    2.    fioparser (git clone https://github.com/jtulak/fio-parser.git)
    3.    python2.x (apt install python2 || yum install python2 )
    4.    numpy (pip2 install numpy)

**Parameters:**

    --w <working directory>
        This should point to a directory on whatever volume you're wanting to test. By default it points to /ontap/working,
        which means it expects you to have a netapp nfs volume mounted to /ontap

    --o <output directory>
        Where you want the results output to

**Example:**

      ./fioparser.sh --w /zfs/working --o /zfs/output

      In the above example, I am testing an FSX for OpenZFS volume mounted to /zfs

**Notes:**

  This takes an hour to run. The part that says "for i in 1 2 3 4 ..." those numbers are talking about the IO depth. 
  You could reduce the runtime of this to 30 min or so by capping it at 10, or 15 min by capping it at 5, but you get
  less information about how more heavy-hitting workloads will behave

## **sso-auth.py**
[**[Back to Top]**](#aws-admin-scripts)

This script will use your AWS IAM Identity Center (Successor to AWS Single Sign-On) account to generate temporary
credentials within your local AWS CLI client as well as set up matching profiles. 

NOTE: The first profile it injects will be the default profile. Subsequent profiles will be formatted as a(account name)

This is useful when you need to run other scripts in this repo across dozens of accounts in an Organization as:
    
    1.  it saves you the manual effort of creating all the profiles
    2.  it improves security by not saving permanent credentials to local files

**Prerequisites:**

    1.  awscliv2 
            NOTE: awscli v1 will not work as it cannot do "aws configure sso-session"      
    2.  boto3

**Required Parameters:**

    -r or --region [String]
        AWS region to use
    
    -d or --defaultrole [String]
        SSO default role to use

**Optional Parameters:**

    -o or --overwrite [True/False]
        script will OVERWRITE your ~/.aws/config and ~/.aws/credentials files
        
        if you do not use this option, the config and credentials files will appear in the local directory

**Procedure to use:**

    1.  aws configure sso-session
        (walk through the dialog)
    2.  aws sso login --your_sso_session_name
        (walk through the dialog and choose the MPA of your Org)

![image](https://user-images.githubusercontent.com/112027478/220894542-900125e1-1fa5-49ea-8685-0c7a870b1274.png)
