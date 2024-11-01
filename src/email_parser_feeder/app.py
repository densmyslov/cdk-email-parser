import json
import pandas as pd
from io import BytesIO
import boto3
import os

s3_client = boto3.client('s3')
stepfunctions_client = boto3.client('stepfunctions')
state_machine_arn = os.environ.get('STATE_MACHINE_ARN')


def lambda_handler(event, context):
    
    bucket_name = os.environ.get('BUCKET')
    print(f"bucket_name: {bucket_name}")
    key = 'service_emails.parquet'
    print(f"key: {key}")
    service_emails_df = pd_read_parquet(s3_client, bucket_name, key, columns=None)
    print(f"service_emails_df: {service_emails_df.shape}")
    if not service_emails_df.empty:
    
        # Convert DataFrame rows into a list of tuples
        tuples_list = [tuple(x) for x in service_emails_df[['user_email', 'user_id', 'service_email', 'email_key']].to_numpy()]
        print(f"tuples_list: {len(tuples_list)}")
        # Define the input to the state machine (list of tuples)
        state_machine_input = {
                                'tuples_list': tuples_list
                                }
        response = stepfunctions_client.start_execution(
                                                        stateMachineArn=state_machine_arn,
                                                        input=json.dumps(state_machine_input)
                                                        )
                                                        
        print(f"State machine execution started: {response}")
                            
        return {
            'statusCode': 200,
            'body': json.dumps('State machine triggered successfully.')
        }
    else:
        print("service_emails_df empty")
        return {
            'statusCode': 200,
            'body': json.dumps('State machine not triggered; service_emails_df empty')
        }

#=========================FUNCTIONS===============================
def pd_read_parquet(_s3_client, bucket, key, columns=None):
    try:
        obj = _s3_client.get_object(Bucket=bucket, Key=key)
        buffer = BytesIO(obj['Body'].read())
        if columns:
            return pd.read_parquet(buffer, columns=columns)
        else:
            return pd.read_parquet(buffer)
    except:
        return pd.DataFrame()