#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_email_parser.cdk_email_parser_stack import CdkEmailParserStack
from aws_cdk import App, Environment
from cdk_email_parser.cdk_email_parser_stack import CdkEmailParserStack  # Your stack import



    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

prod_env=Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
                             region=os.getenv('CDK_DEFAULT_REGION'))

stage_env=Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), 
                             region='us-east-2')

    # Instantiate stacks for each environment

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    #env=cdk.Environment(account='123456789012', region='us-east-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html

app = App()

# Instantiate stacks for each environment
CdkEmailParserStack(app, "CdkEmailParserStack-Stage", env=stage_env)
CdkEmailParserStack(app, "CdkEmailParserStack-Prod", env=prod_env)

app.synth()
