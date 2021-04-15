#!/usr/bin/python

import sys
import boto3

if len(sys.argv) != 7:
    print("Invalid parameters")
    sys.exit(-1)

op = sys.argv[1]
credentials = sys.argv[3]
record = sys.argv[4]
domain = sys.argv[5]
ip_address = sys.argv[6]

if credentials.startswith("arn:aws:iam"):
    sts_client = boto3.client('sts')

    assumed_role_object=sts_client.assume_role(
        RoleArn="arn:aws:iam::account-of-role-to-assume:role/name-of-role",
        RoleSessionName="AssumeRoleSession1"
    )

    credentials=assumed_role_object['Credentials']

    route53=boto3.client(
        'route53',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
    )
elif credentials.find(":") != -1:
    parts = credentials.split(":")
    route53=boto3.client(
        'route53',
        aws_access_key_id=parts[0],
        aws_secret_access_key=parts[1]
    )
else:
    print("Invalid credentials")
    sys.exit(-2)

zone = route53.list_hosted_zones_by_name(DNSName=domain)["HostedZones"][0]

if op == "create":
    action = "UPSERT"
else:
    action = "DELETE"

response = route53.change_resource_record_sets(
    HostedZoneId=zone['Id'],
    ChangeBatch={
        'Changes': [
            {
                'Action': action,
                'ResourceRecordSet': {
                    'Name': "%s.%s" % (record, domain),
                    'Type': 'A',
                    'TTL': 300,
                    'ResourceRecords': [{'Value': ip_address}]
                }
            }
        ]
    })

print(response)
sys.exit(0)