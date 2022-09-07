# admin-scripts

Misc infrastructure management utilities

Authored **independently** by myself, not officially by Amazon Web Services.  Meant to serve as examples/starting points for further customization.  No warranty express or implied.  

ec2-ssm-by-region.py
--------------------
meant to help track down and diagnose EC2 instances that are not properly reporting in to SSM.
		
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
meant to figure out what the maintenance windows are set to across deployed rds instances in both UTC and local time

![image](https://user-images.githubusercontent.com/112027478/188876917-8c506f5a-a271-4dd0-928e-fe5c96e2d758.png)

**To produce the above example (multiple regions rolled into one CSV):**

    python ec2-instances-in-ssm-by-region.py -r us-east-1 -f True > mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r ap-southeast-1 >> mycsv.csv
    python ec2-instances-in-ssm-by-region.py -r ap-northeast-1 >> mycsv.csv

        - The example above puts the data for several European regions into one CSV
        - Notice the first one has the "-f True" parameter set, which adds the column headers
        - It also uses a single > whereas the subsequent ones use >> to redirect output to the file
