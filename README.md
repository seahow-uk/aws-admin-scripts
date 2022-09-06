# admin-scripts

Misc infrastructure management utilities

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
