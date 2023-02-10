# aws-admin-scripts

Misc infrastructure management utilities for use with the AWS platform

Authored **independently** by myself, not officially by any employer of mine, past or present.  Meant to serve as examples/starting points for further customization.  No warranty express or implied.  

admin-instance.yaml
--------------------
CloudFormation template that will spin up an Amazon Linux 2 instance with SSM and CloudWatch agents + everything needed to run these scripts.  It also creates a log group in CloudWatch and streams important logs to it.  Further, the al2-desktop-installer.sh script mentioned below will be run as part of the setup.  Refer to that section for details.

**NOTE:** This repo gets cloned to /opt/aws/aws-admin-scripts .  As root, you should be able to cd to that directory and start executing scripts.

![image](https://user-images.githubusercontent.com/112027478/206909795-ffd9e330-9d51-4692-b30e-25559229ff63.png)

**Required parameters:**

    KeyPair - Select an EC2 KeyPair in that region

    Subnet - Select a Subnet in the VPC you would like to deploy this instance to

    SecurityGroup - Select a Security Group you would like to attach to this instance

    InstanceProfile - An IAM Role that has permissions to send messages to EC2, post CloudWatch Metrics, and communicate with SSM

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

al2-desktop-installer.sh
--------------------
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

ec2-ssm-by-region.py
--------------------
track down and diagnose EC2 instances that are not properly reporting in to SSM.
		
![image](https://user-images.githubusercontent.com/112027478/186730232-7a337b49-529c-4d80-af6e-1cdc6463babd.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python3 ec2-instances-in-ssm-by-region.py -r eu-west-1 -f True > mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r eu-west-2 >> mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r eu-west-3 >> mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r eu-north-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

rds-maintenance-windows.py
--------------------
figure out what the maintenance windows are set to across deployed rds instances in both UTC and local time

![image](https://user-images.githubusercontent.com/112027478/188876917-8c506f5a-a271-4dd0-928e-fe5c96e2d758.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python3 ec2-instances-in-ssm-by-region.py -r us-east-1 -f True > mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r ap-southeast-1 >> mycsv.csv
    python3 ec2-instances-in-ssm-by-region.py -r ap-northeast-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

ebs-discover-stale-volumes.py
--------------------
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

ebs-snapshot-to-archive.py
--------------------
given a list of volume-ids in a file (one per line, no other characters), this will snapshot the volumes in question, wait for that to finish, then move the snapshots to the archive tier.  The idea here is you want to take one last snapshot for the record before deleting a list.

![image](https://user-images.githubusercontent.com/112027478/207862481-bde0fd32-0919-4416-8587-2987bc06bb96.png)

**To produce the above example:**

    python3 ebs-snapshot-to-archive.py -f ./my-volume-list.txt -p prod -r eu-west-1

        - The example above reads a file called my-volume-list.txt in the current directory
        - Notice it has the -p parameter set, this means it will use the "prod" profile from ~/.aws/credentials
        - Finally, the region has to be specified unless you are operating on us-east-1

