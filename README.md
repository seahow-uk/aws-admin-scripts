# aws-admin-scripts

Misc infrastructure management utilities for use with the AWS platform

Authored **independently** by myself, not officially by any employer of mine, past or present.  Meant to serve as examples/starting points for further customization.  No warranty express or implied.  

ec2-ssm-by-region.py
--------------------
track down and diagnose EC2 instances that are not properly reporting in to SSM.
		
![image](https://user-images.githubusercontent.com/112027478/186730232-7a337b49-529c-4d80-af6e-1cdc6463babd.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python ec2-instances-in-ssm-by-region.py -r eu-west-1 -f True > mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r eu-west-2 >> mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r eu-west-3 >> mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r eu-north-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

rds-maintenance-windows.py
--------------------
figure out what the maintenance windows are set to across deployed rds instances in both UTC and local time

![image](https://user-images.githubusercontent.com/112027478/188876917-8c506f5a-a271-4dd0-928e-fe5c96e2d758.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python ec2-instances-in-ssm-by-region.py -r us-east-1 -f True > mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r ap-southeast-1 >> mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r ap-northeast-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

ebs-discover-stale-volumes.py
--------------------
lists all ebs volumes in a given region that are unattached.  denotes which of those volumes have snapshot(s) in the Archive tier, and if they do the date of the most recent example of such.

![ebs-snaps](https://user-images.githubusercontent.com/112027478/201394313-691ff847-9636-4598-bd5e-97ba5c0d0a16.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python ebs-discover-stale-volumes.py -r eu-west-1 -f True > mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-west-2 >> mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-west-3 >> mycsv.csv
    python ebs-discover-stale-volumes.py -r eu-north-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file

al2-desktop-installer.sh
--------------------
installs and configures MATE + VNC (plus all desktop utilities) for an EC2 instance running Amazon Linux 2 (only)

![image](https://user-images.githubusercontent.com/112027478/204065554-7a3b5585-87b0-4562-8c7a-c28dd8ca0ab0.png)

**Optional parameters:**

    --p <password> 
        VNC password will be set to AWS@todaysdate (in this format: AWS@yyyymmdd) unless you specify your own
        for instance, were I to not supply a password and run the script on Nov 26, 2022 it would
        set the VNC login password to "AWS@20221126".  This is obviously insecure and meant for labs only

    --r <runasuser>
        VNC will run as root unless you tell it a different user to run as 

    example:
        ./al2-desktop.sh --p 0neD1rect10nRulez2001 --r ec2-user
