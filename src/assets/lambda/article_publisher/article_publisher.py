import json
import openai
import logging
import boto3
import requests
from html.parser import HTMLParser
import random
import tweepy


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    try:
        # Create a Boto3 session
        logger.debug("Creating Boto3 session.")
        session = boto3.Session()

        # Create a client for the AWS Pricing API
        logger.debug("Creating AWS Pricing client.")
        pricing_client = session.client("pricing", region_name="us-east-1")

        # Get the first page of service results
        logger.info("Fetching AWS services.")
        response = pricing_client.describe_services()

        if "Services" not in response:
            logger.error("No services found in the response.")
            return None

        # Extract the service names from the response
        services = [service["ServiceCode"] for service in response["Services"]]

        # Handle pagination to get additional services
        while "NextToken" in response:
            logger.debug("Fetching additional service results.")
            response = pricing_client.describe_services(NextToken=response["NextToken"])
            services.extend(
                [service["ServiceCode"] for service in response["Services"]]
            )

        logger.debug(f"Found {len(services)} services.")
        return services

    except Exception as e:
        logger.error(f"An error occurred retreiving services from AWS: {e}")
        return None


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
        return None
    return response["Parameter"]["Value"]


# Generate article using OpenAI API
def generate_article(service):
    try:
        logger.info(f"Attempting to generate article for AWS service: {service}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a world-class technology blog writer capable of generating content in HTML format.",
                },
                {
                    "role": "user",
                    "content": f"Please write a blog post I can post on Medium about the AWS service {service}. The blog should include the following sections: 1) Introduction, 2) Key Features, 3) Benefits of Using the Service, 4) Getting Started, and 5) Conclusion. The blog should have an educational tone and be targeted at developers and tech enthusiasts. Please include a call to action at the end of the blog encouraging readers to subscribe. Conclude the article with 'Subscribe for more: https://cullancarey.medium.com/subscribe. Thanks for reading, Cullan Carey.' The blog should be ready to post, without the need for editing, and formatted in HTML.",
                },
            ],
            max_tokens=1000,
            temperature=0.7,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0.6,
        )

        if "choices" in response and len(response["choices"]) > 0:
            blog_content = response["choices"][0]["message"]["content"]
            logger.debug("Successfully generated article content.")
            logger.debug(
                blog_content
            )  # Or use logger.info based on how much detail you want in the logs
            return blog_content
        else:
            logger.warning(
                f"Received unexpected response from OpenAI API. No 'choices' in the response. Api response: {response}"
            )
            return None
    except Exception as e:
        logger.error(
            f"An unknown error occurred while generating the article: {str(e)}"
        )
        return None


def publish_article(title, content, medium_api_token, medium_user_id):
    headers = {
        "Authorization": f"Bearer {medium_api_token}",
        "Content-Type": "application/json",
    }
    tags = [
        "AWS",
        "Cloud Computing",
        "GPT-3",
        "Artificial Intelligence",
        "Automation",
        "Python",
        "Boto3",
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
        logger.info(f"Attempting to publish article with title: {title}")
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 201:
            logger.info(f"Successfully published article with title: {title}")
            article_url = response.json().get("data", {}).get("url", None)
            logger.debug(f"Article URL: {article_url}")
            return article_url
        elif response.status_code == 400:
            logger.warning(f"Bad request: {response.content}")
            return None
        elif response.status_code == 401:
            logger.warning(f"Unauthorized: {response.content}")
            return None
        elif response.status_code == 403:
            logger.warning(f"Forbidden: {response.content}")
            return None
        else:
            logger.error(
                f"Failed to publish article, received status code {response.status_code}: {response.content}"
            )
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to publish article due to network error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unknown error occurred while publishing the article: {e}")
        return None


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

    try:
        logger.info(f"Attempting to share article link {article_url} on LinkedIn.")
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 201:
            logger.info("Successfully shared the article link on LinkedIn.")
        elif response.status_code == 400:
            logger.warning(f"Bad request: {response.content}")
        elif response.status_code == 401:
            logger.warning(f"Unauthorized: {response.content}")
        elif response.status_code == 403:
            logger.warning(f"Forbidden: {response.content}")
        else:
            logger.error(
                f"Failed to share article link on LinkedIn, received status code {response.status_code}: {response.content}"
            )
            return {
                "statusCode": 500,
                "body": f"Failed to share article link on LinkedIn, received status code {response.status_code}: {response.content}",
            }

    except Exception as e:
        logger.error(
            f"An unknown error occurred while sharing the article link on LinkedIn: {e}"
        )
        return {
            "statusCode": 500,
            "body": f"An unknown error occurred while sharing the article link on LinkedIn: {e}",
        }


def post_tweet(tweet_content):
    try:
        logger.info("Attempting to create Twitter client.")

        client_id = get_param("cullan_twitter_api_key")
        access_token = get_param("cullan_twitter_access_token")
        access_token_secret = get_param("cullan_twitter_access_secret_token")
        client_secret = get_param("cullan_twitter_secret_key")

        # Check for empty credentials
        if not all([client_id, access_token, access_token_secret, client_secret]):
            logger.error("One or more Twitter API credentials are missing.")
            return {
                "statusCode": 500,
                "body": "One or more Twitter API credentials are missing.",
            }

        # Create API object
        twitter_client = tweepy.Client(
            consumer_key=client_id,
            consumer_secret=client_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

        # Validate client creation
        if not twitter_client:
            logger.error("Failed to create Twitter client.")
            return {
                "statusCode": 500,
                "body": f"An unknown error occurred while attempting to create twitter client: {e}",
            }

        # Attempt to post the tweet
        logger.info(f"Attempting to send tweet with content: {tweet_content}")
        response = twitter_client.create_tweet(text=tweet_content)
    except Exception as e:
        logger.error(f"An unknown error occurred while attempting to post tweet: {e}")
        return {
            "statusCode": 500,
            "body": f"An unknown error occurred while attempting to post tweet: {e}",
        }
    else:
        if response:
            logger.info(f"Tweet posted successfully! Tweet ID: {response}")
        else:
            logger.warning("Tweet was not posted, and no error was raised.")


def lambda_handler(event, context):
    try:
        logger.info("Lambda function initiated.")

        # Retrieve parameters
        logger.info("Retrieving API tokens and parameters.")
        MEDIUM_API_TOKEN = get_param(param_name="medium_api_token")
        MEDIUM_USER_ID = get_param(param_name="medium_user_id")
        LINKEDIN_ACCESS_TOKEN = get_param(param_name="linkedin_access_token")
        openai.api_key = get_param(param_name="openai_api_token")

        if not all(
            [MEDIUM_API_TOKEN, MEDIUM_USER_ID, LINKEDIN_ACCESS_TOKEN, openai.api_key]
        ):
            logger.error("One or more required parameters are missing.")
            return {"statusCode": 400, "body": "Bad Request: Missing parameters."}

        # Get list of services
        service_list = get_services()

        if service_list is None:
            logger.error("Error retrieving services from AWS.")
            return {
                "statusCode": 500,
                "body": "Internal Server Error: FError retrieving services from AWS.",
            }

        # Generate an article
        article_content = generate_article(service=random.choice(service_list))

        if article_content is None:
            logger.error("No blog generated. Exiting...")
            return {
                "statusCode": 500,
                "body": "Internal Server Error: Failed to generate article from open ai.",
            }

        parser = MyHTMLParser()
        parser.feed(article_content)
        title = parser.title

        # Publish the article on Medium and get the article URL
        article_url = publish_article(
            title=title,
            content=article_content,
            medium_api_token=MEDIUM_API_TOKEN,
            medium_user_id=MEDIUM_USER_ID,
        )

        if article_url is None:
            logger.error("Failed to publish article on Medium.")
            return {
                "statusCode": 500,
                "body": "Internal Server Error: Failed to publish article on Medium.",
            }

        post_content = (
            "Check out my latest blog on Medium written by ChatGPT! "
            "#AWS #CloudComputing #OpenAI #GPT3 #Medium #ArtificialIntelligence "
            "#LinkedIn #Python #Boto3 #Automation #Programming #DevOps #Serverless #NLP #MachineLearning"
        )

        # Share on LinkedIn
        share_on_linkedin(
            article_url=article_url,
            title=title,
            linkedin_access_token=LINKEDIN_ACCESS_TOKEN,
            post_content=post_content,
        )

        # Post tweet
        post_tweet(tweet_content=f"{post_content}\n{article_url}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {"statusCode": 500, "body": f"Internal Server Error: {e}"}

    logger.info("Lambda function completed successfully.")
    return {
        "statusCode": 200,
        "body": "Successfully published article and shared on social media.",
    }
