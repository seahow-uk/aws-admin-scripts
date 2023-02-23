#!/usr/bin/python3

"""
https://github.com/seahow-uk/aws-admin-scripts
by: Ash Stirling 
Feb 2023

Purpose: This script will use your AWS SSO credentials to generate temporary local credentials
and AWS CLI profiles per-account for all the AWS accounts your SSO session has access to.

This is very handy if you have dozens of AWS accounts and you want to loop over all of them in 
a python script - without having to hand-configure dozens of AWS CLI profiles on your linux box.

Prerequisites: 

    1.  awscliv2 

        NOTE: awscli v1 will not work as it cannot do "aws configure sso-session"

        - newer fedora-derived distributions should already have or be able to yum install v2 via EPEL repo

        - ubuntu and other debians will likely get v1 by default

        - to see what version you have, do "aws --ver". If it comes back < 2.x, you need to fix that

           Option 1: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

           Option 2: https://pypi.org/project/awscliv2/          

    2.  boto3

        pip install boto3

Procedure:

    1.  aws configure sso-session

        a.  NOT "aws configure sso"
        b.  walk through the dialog

    2.  aws sso login

        a.  walk through the dialog and choose the MPA

    3.  python3 ./sso-auth.py -d <role you want to default to> -r <your SSO region>
    
        a.  defaultrole: This is here because you might have several roles and we need to know which one
            to use to make temp creds fore in the AWS CLI config

        b.  region: You need to specify the region your SSO service is set up in

**NOTE** 

    This script will delete your current local AWS CLI profile/credential configuration!!

"""

import boto3
import os
from stat import *
import json
import argparse

def setup_args():
    parser = argparse.ArgumentParser(
        description='Optional arguments')

    parser.add_argument('-d', '--defaultrole',
                        required=True,
                        action='store',
                        help='Name of the default Role')
    
    parser.add_argument('-r', '--region',
                        required=True,
                        action='store',
                        help='Name of the Region')

    return (parser.parse_args()) 

def getAccessToken():
  dir = os.path.expanduser('~/.aws/sso/cache')
  
  mostrecent=""
  timestamp=0

  for f in os.listdir(dir):
    pathname = os.path.join(dir, f)
    statinfo = os.stat(pathname)
    if S_ISREG(statinfo.st_mode):
      if statinfo.st_mtime > timestamp:
        mostrecent = pathname
        timestamp = statinfo.st_mtime

  if mostrecent == "":
    exit("Unable to find access token; maybe you need to log in with 'aws sso login'.")

  jobj = json.load(open(mostrecent))
  return jobj['accessToken']

def main():
  args = setup_args()

  defaultRole = args.defaultrole
  defaultRegion = args.region

  accessToken = getAccessToken() 

  if (accessToken == None):
    exit( "Unable to get accounts; no access token")

  session = boto3.Session(region_name=defaultRegion)
  sso = session.client('sso')

  accounts = sso.list_accounts(maxResults=1000,accessToken=accessToken)['accountList']
  
  with open('config', 'w', encoding='utf-8') as f:
    f.write("")

  with open('credentials', 'w', encoding='utf-8') as f:
    f.write("")
    

  for a in accounts:
    print(a)
    roleList = sso.list_account_roles(maxResults=20,accessToken=accessToken,accountId=a['accountId'])['roleList']

    roles = []
    for r in roleList:
      roles.append(r['roleName'])

    print(roles)
    if defaultRole not in roles:
      print(f"Not assigned a role named {defaultRole} in {a['accountName']}")
      next
    
    creds = sso.get_role_credentials( roleName=defaultRole, accountId=a['accountId'], accessToken=accessToken)

    with open('config','a',encoding='utf-8') as f:
      f.write( f"[profile {a['accountName']}]\n")
      f.write( f"output=json\n")
      f.write( f"region=eu-west-1\n\n")

    with open('credentials', 'a', encoding='utf-8') as f:
      f.write( f"[{a['accountName']}]\n")
      f.write( f"aws_access_key_id={creds['roleCredentials']['accessKeyId']}\n")
      f.write( f"aws_secret_access_key={creds['roleCredentials']['secretAccessKey']}\n")
      f.write( f"aws_session_token={creds['roleCredentials']['sessionToken']}\n\n")

if __name__ == "__main__":
    main()
