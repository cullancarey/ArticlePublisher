Certainly! Below is your updated README file, incorporating the new `lambda_handler` function in the Overview section.

---

# Python Article Publisher with AWS and OpenAI

This repository contains a Python script to automate the process of generating and publishing articles about AWS services. The script leverages AWS services and OpenAI's GPT-3 to automate the entire workflow.

## Table of Contents

- [Dependencies](#dependencies)
- [Overview](#overview)
  - [Logging](#logging)
  - [Custom HTML Parser](#custom-html-parser)
  - [Fetching AWS Services](#fetching-aws-services)
  - [Fetching Parameters from AWS SSM](#fetching-parameters-from-aws-ssm)
  - [Article Generation with OpenAI GPT-3](#article-generation-with-openai-gpt-3)
  - [Publishing Article to Medium](#publishing-article-to-medium)
  - [Sharing Article on LinkedIn](#sharing-article-on-linkedin)
  - [Tweeting Article on Twitter](#tweeting-article-on-twitter)
  - [AWS Lambda Handler](#aws-lambda-handler)
- [Usage](#usage)
- [License](#license)
- [Contact](#contact)

## Dependencies

- Python
- `boto3`: For AWS SDK
- `requests`: For making HTTP requests
- `openai`: For OpenAI GPT-3
- `logging`: For logging
- `json`: For JSON manipulation
- `html.parser`: For parsing HTML
- `tweepy`: For Twitter API
- `random`: For generating random numbers

## Overview

### Logging

The script employs Python's built-in `logging` library for capturing various events and milestones in the script's operation.

### Custom HTML Parser

A custom HTML parser (`MyHTMLParser`) is implemented by extending Python's built-in `HTMLParser` class. The parser is designed to fetch the title of an HTML document.

### Fetching AWS Services

The function `get_services()` utilizes `boto3` to fetch the list of AWS services and their details. It handles API pagination and returns a list of services.

### Fetching Parameters from AWS SSM

The function `get_param(param_name: str)` fetches a specific parameter from AWS Systems Manager Parameter Store.

### Article Generation with OpenAI GPT-3

The script uses the `generate_article(service)` function to interact with OpenAI's GPT-3 API and generate an article based on a given AWS service. This function is designed to return the article content as a string.

### Publishing Article to Medium

The `publish_article(title, content, medium_api_token, medium_user_id)` function is used to publish the generated articles to Medium via the Medium API.

### Sharing Article on LinkedIn

The `share_on_linkedin(article_url, title, linkedin_access_token, post_content)` function is employed to share the generated article on LinkedIn via LinkedIn's API. It handles authorization and posting and logs the activity.

### Tweeting Article on Twitter

The `post_tweet(tweet_content)` function is used to post a tweet containing the article's link to Twitter. The function uses the `tweepy` library to interact with Twitter's API.

### AWS Lambda Handler

The `lambda_handler(event, context)` function serves as the AWS Lambda function entry point. It orchestrates all the above functions to automate the article creation and sharing process. The function performs logging, retrieves required API keys and parameters, generates an article based on a random AWS service, publishes it to Medium, and then shares it on LinkedIn and Twitter.