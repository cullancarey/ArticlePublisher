import json
import openai
import logging
import boto3
import os
import requests
from html.parser import HTMLParser


# Set up logging
logger = logging.getLogger()
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
def generate_article():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a world class technology blog writer.",
            },
            {
                "role": "user",
                "content": "Please write an article I can post on Medium about a popular AWS topic. format it in html please.",
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
    payload = json.dumps(
        {
            "title": title,
            "content": content,
            "contentFormat": "html",
            "tags": ["AWS", "Cloud Computing", "Technology"],
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


def share_on_linkedin(article_url, title, linkedin_access_token):
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
                    "shareCommentary": {
                        "text": "Check out my latest blog on Medium written by ChatGPT!"
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": "Learning more about AWS by using chatGpt to write blogs for Medium!"
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


def lambda_handler(event, context):
    # Retrieve parameters
    MEDIUM_API_TOKEN = get_param(param_name="medium_api_token")
    MEDIUM_USER_ID = get_param(param_name="medium_user_id")
    LINKEDIN_ACCESS_TOKEN = get_param(param_name="linkedin_access_token")

    # Initialize OpenAI API
    openai.api_key = get_param(param_name="openai_api_token")

    # Generate an article
    article_content = generate_article()

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

    # If successfully published on Medium, share on LinkedIn
    if article_url:
        share_on_linkedin(
            article_url=article_url,
            title=title,
            linkedin_access_token=LINKEDIN_ACCESS_TOKEN,
        )


lambda_handler(event=None, context=None)
