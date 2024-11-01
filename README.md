
# cdk-email-parser

`cdk-email-parser` is an AWS CDK (Cloud Development Kit) project designed to deploy an infrastructure for parsing emails using Lambda functions, Step Functions, S3 storage, and EventBridge scheduling. This setup is ideal for applications that process and analyze email data within a serverless architecture on AWS.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup and Deployment](#setup-and-deployment)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

This project uses AWS CDK to automate the deployment of serverless resources to AWS, enabling a scalable and efficient email parsing service. The service includes:
- **Lambda Functions**: One for feeding data into a Step Function, and another for parsing emails.
- **Step Functions**: Used to orchestrate and process tasks as part of the email parsing workflow.
- **S3 Bucket**: To store email data and any intermediate results.
- **EventBridge Rule**: To trigger the Lambda function on a defined schedule.

## Architecture

The following AWS resources are deployed by this project:
- **S3 Bucket**: Used to store email files and any related assets.
- **Lambda Functions**:
  - `EmailParserFunction`: Parses email data and processes it as needed.
  - `EmailParserFeederFunction`: Triggers the state machine to start processing.
- **Step Functions**: A state machine that orchestrates the parsing process.
- **EventBridge Rule**: A cron-based rule to schedule the feeder function to run periodically.

## Prerequisites

- **AWS Account**: You need an AWS account to deploy the resources.
- **Node.js**: Ensure Node.js is installed (recommended version 18.x).
- **AWS CDK**: Install the AWS CDK globally: `npm install -g aws-cdk`
- **Python 3.8+**: Required for Lambda functions and CDK Python dependencies.

## Setup and Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/cdk-email-parser.git
cd cdk-email-parser
```

### 2. Install Dependencies
Set up the Python environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use .venv\Scripts\activate
pip install -r requirements.txt
```
### 3. Configure AWS Credentials
Ensure your AWS credentials are configured. You can use aws configure or set up a profile as described in the [AWS CLI documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html).  

### 4. Define Environment Context in cdk.json
In cdk.json, specify environment-specific variables under the context key, such as bucket_name for different environments:
```json
{
  "context": {
    "env": {
      "stage": {
        "bucket_name": "your-stage-bucket-name"
      },
      "prod": {
        "bucket_name": "your-prod-bucket-name"
      }
    }
  }
}
```
to be continued ...
