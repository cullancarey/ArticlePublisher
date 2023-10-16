# Python CDK Stack for Automated Article Publishing

This repository contains a Python CDK stack for automating the process of article publishing. The stack deploys an AWS Lambda function, IAM policies, and a CloudWatch Event Rule to publish articles at a scheduled time.

## Table of Contents

- [ArticlePublisherStack](#articlepublisherstack)

## ArticlePublisherStack

This stack sets up an automated workflow for publishing articles. The Lambda function is responsible for publishing articles and sharing them on social media platforms like LinkedIn and Twitter.

### Parameters

- `medium_api_token`: SSM parameter for the Medium API token.
- `medium_user_id`: SSM parameter for the Medium user ID.
- `openai_api_token`: SSM parameter for the OpenAI API token.
- `linkedin_access_token`: SSM parameter for the LinkedIn access token.
- `cullan_twitter_api_key`: SSM parameter for the Twitter API key.
- `cullan_twitter_access_token`: SSM parameter for the Twitter access token.
- `cullan_twitter_access_secret_token`: SSM parameter for the Twitter access secret token.
- `cullan_twitter_secret_key`: SSM parameter for the Twitter secret key.

### Features

- **Lambda Function**: Deploys a Dockerized Lambda function for article generation and sharing. This function runs on a schedule, and its logs are retained for one year.
  
- **IAM Policy**: Assigns an IAM policy to the Lambda function, allowing it to describe AWS pricing services.
  
- **SSM Parameter Access**: The Lambda function is granted read access to specified SSM parameters. This includes API tokens and other sensitive information for Medium, LinkedIn, OpenAI, and Twitter.

- **Scheduled Trigger**: Adds a CloudWatch Events Rule that triggers the Lambda function daily at 1:00 PM.