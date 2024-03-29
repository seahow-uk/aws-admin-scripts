#!/usr/bin/python3

"""
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

        a.  walk through the dialog

    2.  aws sso login --sso-session <SSO session name from step 1>

        a.  walk through the dialog and choose the MPA

    3.  python3 ./sso-auth.py -d <role you want to default to> -r <your SSO region> -o True
    
        a.  defaultrole: This is here because you might have several roles and we need to know which one
            to use to make temp creds for in the AWS CLI config

        b.  region: You need to specify the region your SSO service is set up in

        c.  overwrite: if you add the -o True option, the script will OVERWRITE your ~/.aws/config and credentials files
            if you do not include it, the credentials and config files will appear in the local directory

"""

import boto3
import os
from stat import *
import json
import argparse

def setup_args():
    parser = argparse.ArgumentParser(
        description='Arguments')

    parser.add_argument('-d', '--defaultrole',
                        required=True,
                        action='store',
                        help='Name of the default Role')
    
    parser.add_argument('-r', '--region',
                        required=True,
                        action='store',
                        help='Name of the Region')

    parser.add_argument('-o', '--overwrite',
                        required=False,
                        action='store',
                        help='True/False')

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
  
  if (args.overwrite):
    if args.overwrite == "True" or args.overwrite == "true":
      defaultPath = os.path.expanduser('~/.aws')
    else:
      defaultPath = ""
  else:
    defaultPath = ""
    
  credentialsFile = os.path.join(defaultPath, 'credentials')
  configFile = os.path.join(defaultPath, 'config')

  accessToken = getAccessToken() 

  if (accessToken == None):
    exit( "Unable to get accounts; no access token")

  session = boto3.Session(region_name=defaultRegion)
  sso = session.client('sso')

  accounts = sso.list_accounts(maxResults=1000,accessToken=accessToken)['accountList']
  
  with open(credentialsFile, 'w', encoding='utf-8') as f:
    f.write("")

  with open(configFile, 'w', encoding='utf-8') as f:
    f.write("")
    
  firstAccount = 1

  for a in accounts:
    print(a)
    roleList = sso.list_account_roles(maxResults=20,accessToken=accessToken,accountId=a['accountId'])['roleList']

    roles = []
    for r in roleList:
      roles.append(r['roleName'])

    print(roles)
    if defaultRole not in roles:
      print(f"Not assigned a role named {defaultRole} in {a['accountName']} - skipping")
      continue
    
    creds = sso.get_role_credentials( roleName=defaultRole, accountId=a['accountId'], accessToken=accessToken)

    if firstAccount == 1:
      profileName = 'default'
      firstAccount = 0
    else:
      profileName = a['accountName']

    with open(configFile,'a',encoding='utf-8') as f:
      f.write( f"[profile {profileName}]\n")
      f.write( f"output=json\n")
      f.write( f"region=eu-west-1\n\n")

    with open(credentialsFile, 'a', encoding='utf-8') as f:
      f.write( f"[{profileName}]\n")
      f.write( f"aws_access_key_id={creds['roleCredentials']['accessKeyId']}\n")
      f.write( f"aws_secret_access_key={creds['roleCredentials']['secretAccessKey']}\n")
      f.write( f"aws_session_token={creds['roleCredentials']['sessionToken']}\n\n")

if __name__ == "__main__":
    main()
