import json
import openai
import logging
import boto3
import os
import requests
from html.parser import HTMLParser
import random
import tweepy


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.recording = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.recording = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.recording = False

    def handle_data(self, data):
        if self.recording:
            self.title = data


def get_services():
    # Create a Boto3 session (this will use your AWS credentials from environment variables, AWS CLI, or IAM role)
    session = boto3.Session()

    # Create a client for the AWS Pricing API
    pricing_client = session.client("pricing", region_name="us-east-1")

    # Get the first page of service results
    response = pricing_client.describe_services()

    # Extract the service names from the response
    services = [service["ServiceCode"] for service in response["Services"]]

    # Handle pagination to get additional services, if there are more than one page of results
    while "NextToken" in response:
        response = pricing_client.describe_services(NextToken=response["NextToken"])
        services.extend([service["ServiceCode"] for service in response["Services"]])

    # Now `services` contains a list of service names
    return services


def get_param(
    param_name: str,
):
    """Function to get parameter value from parameter store"""
    client = boto3.client("ssm")
    try:
        logger.info(f"Retrieving parameter {param_name}...")
        response = client.get_parameter(Name=param_name, WithDecryption=True)
    except Exception as e:
        logger.error(f"Error retrieving parameter: {param_name} with error: {e}")
    return response["Parameter"]["Value"]


# Generate article using OpenAI API
def generate_article(service):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a world class technology blog writer.",
            },
            {
                "role": "user",
                "content": f"Please write an blog I can post on Medium about the AWS service {service}. I am asking you to do this programatically through the api and then posting it to Medium through their api. So I do not have the capability to edit the content you return so I would like it to be as ready to post as possible. Please end the article with 'Subscribe for more: https://cullancarey.medium.com/subscribe. Thanks for reading, Cullan Carey.' Also, format it in html please.",
            },
        ],
        max_tokens=1000,
    )
    blog_content = response["choices"][0]["message"]["content"]
    logger.debug(blog_content)
    return blog_content


def publish_article(title, content, medium_api_token, medium_user_id):
    headers = {
        "Authorization": f"Bearer {medium_api_token}",
        "Content-Type": "application/json",
    }
    tags = [
        "AWS",
        "Cloud Computing",
        "OpenAI",
        "GPT-3",
        "Medium",
        "Artificial Intelligence",
        "LinkedIn",
        "Python",
        "Boto3",
        "Automation",
        "Programming",
        "DevOps",
        "Serverless",
        "NLP",
        "Machine Learning",
    ]

    payload = json.dumps(
        {
            "title": title,
            "content": content,
            "contentFormat": "html",
            "tags": tags,
            "publishStatus": "public",
        }
    )

    url = f"https://api.medium.com/v1/users/{medium_user_id}/posts"

    try:
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 201:
            logger.info(f"Successfully published article with title: {title}")
            article_url = response.json()["data"]["url"]
            return article_url
        else:
            logger.error(f"Failed to publish article: {response.content}")
            return None
    except Exception as e:
        logger.error(f"Failed to publish article to Medium: {e}")


def share_on_linkedin(article_url, title, linkedin_access_token, post_content):
    headers = {
        "Authorization": f"Bearer {linkedin_access_token}",
        "Content-Type": "application/json",
    }

    payload = json.dumps(
        {
            "author": "urn:li:person:NAAxLwhs43",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": post_content},
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": "Learning more about AWS by using ChatGPT to write blogs for Medium!"
                            },
                            "originalUrl": article_url,
                            "title": {"text": title},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
    )

    url = "https://api.linkedin.com/v2/ugcPosts"
    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 201:
        logger.info("Successfully shared the article link on LinkedIn.")
    else:
        logger.error(f"Failed to share article link on LinkedIn: {response.content}")


def post_tweet(tweet_content):
    try:
        logger.info("Creating twitter client.")
        client_id = get_param(f"cullan_twitter_api_key")
        access_token = get_param(f"cullan_twitter_access_token")
        access_token_secret = get_param(f"cullan_twitter_access_secret_token")
        client_secret = get_param(f"cullan_twitter_secret_key")

        # Create API object
        twitter_client = tweepy.Client(
            consumer_key=client_id,
            consumer_secret=client_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        # Post the tweet
        logger.info(f"Sending tweet with content: {tweet_content}")
        response = twitter_client.create_tweet(text=tweet_content)
    except Exception as e:
        logger.error(f"An error occurred creating tweet: {e}")
    else:
        logger.info(f"Tweet posted successfully! Tweet info: {response}")


def lambda_handler(event, context):
    # Retrieve parameters
    MEDIUM_API_TOKEN = get_param(param_name="medium_api_token")
    MEDIUM_USER_ID = get_param(param_name="medium_user_id")
    LINKEDIN_ACCESS_TOKEN = get_param(param_name="linkedin_access_token")

    # Initialize OpenAI API
    openai.api_key = get_param(param_name="openai_api_token")

    # Get list of services
    service_list = get_services()

    # Generate an article
    article_content = generate_article(service=random.choice(service_list))

    parser = MyHTMLParser()
    parser.feed(article_content)
    title = parser.title
    # title = "Demystifying AWS S3: Secure, Scalable, and Simple Storage Solutions"

    # Publish the article on Medium and get the article URL
    article_url = publish_article(
        title=title,
        content=article_content,
        medium_api_token=MEDIUM_API_TOKEN,
        medium_user_id=MEDIUM_USER_ID,
    )
    # article_url = "https://medium.com/@cullancarey/demystifying-aws-s3-secure-scalable-and-simple-storage-solutions-265f3b8c11a0"

    post_content = f"Check out my latest blog on Medium written by ChatGPT! #AWS #CloudComputing #OpenAI #GPT3 #Medium #ArtificialIntelligence #LinkedIn #Python #Boto3 #Automation #Programming #DevOps #Serverless #NLP #MachineLearning"

    # If successfully published on Medium, share on LinkedIn
    if article_url:
        share_on_linkedin(
            article_url=article_url,
            title=title,
            linkedin_access_token=LINKEDIN_ACCESS_TOKEN,
            post_content=post_content,
        )

        post_tweet(tweet_content=f"{post_content}\n{article_url}")
