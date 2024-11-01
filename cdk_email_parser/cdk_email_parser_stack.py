from aws_cdk import (
                        Stack,
                        Duration,
                        aws_lambda as _lambda,
                        aws_iam as iam,
                        aws_stepfunctions as sfn,
                        aws_stepfunctions_tasks as tasks,
                        aws_logs as logs,
                        aws_events_targets as targets,
                        aws_events as events,
                        aws_s3 as s3,
                        RemovalPolicy
                    )
from constructs import Construct

class CdkEmailParserStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Determine environment (based on stack name or context)
        env_name = self.node.try_get_context("env_name") or "stage"
        env_config = self.node.try_get_context("env")[env_name]

        # get bucket_name depending on environment
        bucket_name = env_config.get("bucket_name")
        if not bucket_name:
            raise ValueError(f"bucket_name is not defined for environment: {env_name}")
        
        state_machine_name = "EmailParserStateMachine"

        # Create the S3 bucket
        bucket = s3.Bucket(self, "MyBucket",
            bucket_name=bucket_name,
            removal_policy=RemovalPolicy.DESTROY,  # Optional: for testing only; use RETAIN for prod
            auto_delete_objects=True  # Optional: for testing only
        )

        # Define a Lambda Layer (from a local directory or S3)
        pillow_layer = _lambda.LayerVersion(self, "pillowLayer",
            code=_lambda.Code.from_asset("layers/pillow_layer.zip"),  # Local folder containing the layer
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],  # Specify compatible runtimes
            description="A layer with PIL for my Lambda function",
        )

        # Lambda layer from default layer
        pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, "AWSSDKPandas-Python312",
            layer_version_arn="arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python312:13"
        )

        # Define the Lambda function invoked within the Step Function
        email_parser_function = _lambda.Function(
            self, "EmailParserFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="app.lambda_handler",
            code=_lambda.Code.from_asset("src/email_parser"),
            layers=[pillow_layer],
            memory_size=512,
            timeout=Duration.seconds(720),
            log_retention=logs.RetentionDays.ONE_WEEK,
            environment={
                "BUCKET": bucket_name
            },
            description="This Lambda function parses emails for the email parser service"
        )

        # Grant the Lambda function permissions to access the bucket
        bucket.grant_read_write(email_parser_function)

        # Define the Lambda task for Step Function
        email_parser_task = tasks.LambdaInvoke(self, "InvokeEmailParser",
            lambda_function=email_parser_function
        )
        # Define the state machine

        # Create the Map state
        process_tuples = sfn.Map(self, "ProcessTuples",
            max_concurrency=150,
            items_path="$.tuples_list"
        )

        # Define the task chain within the Map state
        process_tuples.iterator(email_parser_task)

        # Define the state machine
        state_machine = sfn.StateMachine(self, "StateMachine",
            definition_body=sfn.DefinitionBody.from_chainable(process_tuples),  # Use definition_body
            timeout=Duration.minutes(5),
            state_machine_name=state_machine_name
        )
        # Grant permission to Step Functions to invoke the Lambda function
        lambda_invoke_policy = iam.PolicyStatement(
            actions=["lambda:InvokeFunction"],
            resources=[email_parser_function.function_arn]
        )
        
        # Attach the policy to the state machine's role
        state_machine.role.add_to_policy(lambda_invoke_policy)

        # Lambda function which invokes the state machine and feeds email account data into it
        email_parser_feeder_function = _lambda.Function(
            self, "EmailParserFeederFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            layers = [pandas_layer],
            handler="app.lambda_handler",
            code =_lambda.Code.from_asset("src/email_parser_feeder"),
            memory_size = 512,
            timeout=Duration.seconds(30),
            log_retention=logs.RetentionDays.ONE_WEEK,
            environment={
                            "STATE_MACHINE_ARN": state_machine.state_machine_arn,
                            "BUCKET": bucket_name
                        },
            description=f"This Lambda function feeds email account data into the {state_machine_name} and triggers the state machine"
        )

        # Grant the Lambda function permissions to read objects in the bucket
        bucket.grant_read(email_parser_feeder_function)

        # Grant permissions to email_parser_feeder_function to start the Step Function
        state_machine.grant_start_execution(email_parser_feeder_function)

        # Define a cron schedule (e.g., run every day at 12:00 UTC)
        cron_rule = events.Rule(self, "StepFunctionCronRule",
            schedule=events.Schedule.cron(
                minute="0",
                hour="15",      # 12:00 UTC
                day="*",       # every day
                month="*",     # every month
                year="*"       # every year
            )
        )
        # Set the Lambda function as the target for the EventBridge rule
        cron_rule.add_target(targets.LambdaFunction(email_parser_feeder_function))

