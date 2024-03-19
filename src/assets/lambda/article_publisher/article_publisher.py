import json
import os
from openai import OpenAI
import logging
import boto3
import boto3.session
import requests
from html.parser import HTMLParser
import random
import tweepy

logging.basicConfig(level=logging.INFO)
# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a Boto3 session to interact with AWS services
logger.debug("Creating Boto3 session.")
session = boto3.session.Session(region_name="us-east-2")

# Set SNS topic variable from environment
SNS_TOPIC = os.environ.get("SNS_TOPIC_ARN", None)


# Define a custom HTML parser class that inherits from the built-in HTMLParser
class MyHTMLParser(HTMLParser):
    # Initialize the parser
    def __init__(self):
        # Call the constructor of the superclass (HTMLParser)
        super().__init__()

        # A flag to determine whether we are within a <title> tag
        self.recording = False

        # A string to store the data within the <title> tag
        self.title = ""

    # Overridden method to handle the start tag in the HTML document
    def handle_starttag(self, tag, attrs):
        # If the start tag is <title>, set the recording flag to True
        if tag == "title":
            self.recording = True

    # Overridden method to handle the end tag in the HTML document
    def handle_endtag(self, tag):
        # If the end tag is </title>, set the recording flag to False
        if tag == "title":
            self.recording = False

    # Overridden method to handle the data within a tag
    def handle_data(self, data):
        # If we're within a <title> tag, record the data (the title in this case)
        if self.recording:
            self.title = data


def publish_sns(message: str):
    try:
        sns_client = session.client("sns")

        if SNS_TOPIC is not None:
            sns_client.publish(
                TopicArn=SNS_TOPIC,
                Message=message,
                Subject="ArticlePublisher Notification",
            )
            logger.info(f"Successfully published sns message: {message}.")
        else:
            logger.error("SNS topic not found in environment.")
            return None

    except Exception as e:
        logger.error(
            f"An error occurred while publishing message to sns: {message}. Error: {e}"
        )
        return None


def get_services():
    try:
        # Get a list of available services in the specified region
        logger.info("Fetching AWS services.")
        services = session.get_available_services()

        # Log the total number of services found
        logger.debug(f"Found {len(services)} services.")

        return services
    except Exception as e:
        logger.error(f"An error occurred while fetching AWS services: {e}")
        publish_sns(message=f"An error occurred while fetching AWS services: {e}")
        return None


def get_param(param_name: str):
    """
    Function to get a parameter value from AWS Systems Manager Parameter Store.

    Parameters:
    param_name (str): The name of the parameter you want to retrieve.

    Returns:
    str: The parameter value.
    None: If the parameter could not be retrieved.
    """

    # Initialize the boto3 client for SSM (Simple Systems Manager)
    client = boto3.client("ssm")

    try:
        # Log the initiation of the parameter retrieval
        logger.info(f"Retrieving parameter {param_name}...")

        # Make the API call to get the parameter and also decrypt it if needed
        response = client.get_parameter(Name=param_name, WithDecryption=True)

    except Exception as e:
        # Log any errors that occur while trying to retrieve the parameter
        logger.error(f"Error retrieving parameter: {param_name} with error: {e}")
        publish_sns(message=f"Error retrieving parameter: {param_name} with error: {e}")

        # Return None to indicate that the parameter could not be retrieved
        return {
            "statusCode": 400,
            "body": f"Error retrieving parameter: {param_name} with error: {e}",
        }

    # Extract the parameter value from the API response and return it
    return response["Parameter"]["Value"]


# Function to generate an article using OpenAI's GPT-3 API
def generate_article(service):
    try:
        # Log the initiation of the article generation process
        logger.info(f"Attempting to generate article for AWS service: {service}")
        client = OpenAI(api_key=get_param(param_name="openai_api_token"))

        # API call to OpenAI for article generation
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Using the GPT-3.5 model
            messages=[
                {
                    "role": "system",
                    "content": "You are a world-class technology blog writer capable of generating SEO-friendly content in HTML format.",
                },
                {
                    "role": "user",
                    "content": f"Please write an SEO-friendly blog post I can post on Medium about the AWS service {service}. The blog should include the following sections: 1) Introduction, 2) Key Features, 3) Benefits of Using the Service, 4) Getting Started, and 5) Conclusion. The blog should have an educational tone and be targeted at developers and tech enthusiasts. Include meta descriptions, header tags, and relevant keywords for SEO optimization. Please include a call to action at the end of the blog encouraging readers to subscribe. Conclude the article with 'Subscribe for more: https://cullancarey.medium.com/subscribe. Thanks for reading, Cullan Carey.' The blog should be ready to post, without the need for editing, and formatted in HTML.",  # Request details here
                },
            ],
            max_tokens=2000,  # Limiting the response to 1000 tokens
            temperature=0.7,  # Controlling randomness
            top_p=1.0,  # Controlling diversity of the output
            frequency_penalty=0,  # No frequency penalty
            presence_penalty=0.6,  # Some presence penalty to make the output coherent
        )

        # Checking if the 'choices' key exists in the API response and is non-empty
        if response.choices[0].message:
            # Extract the generated article from the API response
            blog_content = response.choices[0].message.content

            # Log the successful article generation
            logger.debug("Successfully generated article content.")
            logger.debug(
                blog_content
            )  # Or use logger.info based on how much detail you want in the logs

            return blog_content
        else:
            # Log a warning if the API response is unexpected
            logger.error(
                f"Received unexpected response from OpenAI API. No 'choices' in the response. Api response: {response}"
            )
            publish_sns(
                message=f"Received unexpected response from OpenAI API. No 'choices' in the response. Api response: {response}"
            )
            return None
    except Exception as e:
        # Log any unknown errors
        logger.error(f"An unknown error occurred while generating the article: {e}")
        publish_sns(
            message=f"An unknown error occurred while generating the article: {e}"
        )
        return None


def generate_linkedin_post_content(service):
    try:
        logger.info("Generating LinkedIn post content.")
        client = OpenAI(api_key=get_param(param_name="openai_api_token"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a social media expert, skilled at creating engaging, fun, and emoji-filled LinkedIn posts.",
                },
                {
                    "role": "user",
                    "content": f"Create a LinkedIn post to promote my new blog article about AWS service '{service}'. No need to link the article because it will be linked through the linkedin post api. The blog post includes the following sections: 1) Introduction, 2) Key Features, 3) Benefits of Using the Service, 4) Getting Started, and 5) Conclusion. Generate a LinkedIn post that encourages people to read the blog post and subscribe to my Medium account. Make sure the post is engaging and includes relevant hashtags.",
                },
            ],
            max_tokens=500,
            temperature=0.7,
            top_p=1.0,
            frequency_penalty=0,
            presence_penalty=0.6,
        )
        # Checking if the 'choices' key exists in the API response and is non-empty
        if response.choices[0].message:
            # Extract the generated article from the API response
            linkedin_post_content = response.choices[0].message.content

            # Log the successful article generation
            logger.debug("Successfully generated linkedin post content.")
            logger.debug(
                linkedin_post_content
            )  # Or use logger.info based on how much detail you want in the logs

            return linkedin_post_content
        else:
            # Log an error if the API response is unexpected
            logger.error(
                f"Received unexpected response from OpenAI API. No 'choices' in the response. Api response: {response}"
            )
            publish_sns(
                message=f"Error occurred in ArticlePublisher: Failed to generate LinkedIn post content from open ai. Api response: {response}"
            )
            return None
    except Exception as e:
        # Log any unknown errors
        logger.error(
            f"An unknown error occurred while generating the linkedin post content: {e}"
        )
        publish_sns(
            message=f"Error occurred in ArticlePublisher: An unknown error occurred while generating the linkedin post content: {e}"
        )
        return None


# Function to publish an article to Medium
def publish_article(title, content, medium_api_token, medium_user_id):
    # Configure HTTP headers for Medium API
    headers = {
        "Authorization": f"Bearer {medium_api_token}",
        "Content-Type": "application/json",
    }

    # Define tags for the Medium post
    tags = [
        "AWS",
        "Cloud Computing",
        "Python",
        "DevOps",
        "Infrastructure As Code",
    ]

    # Prepare the payload with article details
    payload = json.dumps(
        {
            "title": title,
            "content": content,
            "contentFormat": "html",  # Article content format
            "tags": tags,  # Tags for the article
            "publishStatus": "public",  # Make the article public upon publishing
        }
    )

    # URL to post the article to Medium
    url = f"https://api.medium.com/v1/users/{medium_user_id}/posts"

    try:
        # Log the attempt to publish
        logger.info(f"Attempting to publish article with title: {title}")

        # Make a POST request to publish the article
        response = requests.post(url, headers=headers, data=payload)

        # Check response status code to determine the outcome
        if response.status_code == 201:
            logger.info(f"Successfully published article with title: {title}")
            article_url = response.json().get("data", {}).get("url", None)
            logger.debug(f"Article URL: {article_url}")
            return article_url
        elif response.status_code != 201:
            logger.error(
                f"Failed to publish article, received status code {response.status_code}: {response.content}"
            )
            publish_sns(
                message=f"Failed to publish article, received status code {response.status_code}: {response.content}"
            )
            return None

    # Handle specific exceptions
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to publish article due to network error: {e}")
        publish_sns(message=f"Failed to publish article due to network error: {e}")
        return None
    except Exception as e:
        logger.error(f"An unknown error occurred while publishing the article: {e}")
        publish_sns(
            message=f"An unknown error occurred while publishing the article: {e}"
        )
        return None


# Function to share an article on LinkedIn
def share_on_linkedin(article_url, title, linkedin_access_token, post_content):
    # Configure HTTP headers for LinkedIn API
    headers = {
        "Authorization": f"Bearer {linkedin_access_token}",
        "Content-Type": "application/json",
    }

    # Prepare the payload with share details
    payload = json.dumps(
        {
            "author": "urn:li:person:NAAxLwhs43",  # Replace with actual LinkedIn Person URN
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

    # URL to share the article on LinkedIn
    url = "https://api.linkedin.com/v2/ugcPosts"

    try:
        # Log the attempt to share
        logger.info(f"Attempting to share article link {article_url} on LinkedIn.")

        # Make a POST request to share the article
        response = requests.post(url, headers=headers, data=payload)

        # Check response status code to determine the outcome
        if response.status_code == 201:
            logger.info("Successfully shared the article link on LinkedIn.")
        elif response.status_code != 201:
            logger.error(
                f"Failed to share article link on LinkedIn, received status code {response.status_code}: {response.content}"
            )
            publish_sns(
                message=f"Failed to share article link on LinkedIn, received status code {response.status_code}: {response.content}"
            )
            return {
                "statusCode": 500,
                "body": f"Failed to share article link on LinkedIn, received status code {response.status_code}: {response.content}",
            }

    # Handle specific exceptions
    except Exception as e:
        logger.error(
            f"An unknown error occurred while sharing the article link on LinkedIn: {e}"
        )
        publish_sns(
            message=f"An unknown error occurred while sharing the article link on LinkedIn: {e}"
        )
        return {
            "statusCode": 500,
            "body": f"An unknown error occurred while sharing the article link on LinkedIn: {e}",
        }


# Function to post a tweet on Twitter
def post_tweet(tweet_content):
    try:
        # Log an info message before attempting to create the Twitter client
        logger.info("Attempting to create Twitter client.")

        # Retrieve Twitter API credentials from parameter store
        client_id = get_param("cullan_twitter_api_key")
        access_token = get_param("cullan_twitter_access_token")
        access_token_secret = get_param("cullan_twitter_access_secret_token")
        client_secret = get_param("cullan_twitter_secret_key")

        # Create Twitter API client using Tweepy
        twitter_client = tweepy.Client(
            consumer_key=client_id,
            consumer_secret=client_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

        # Validate if the Twitter client was successfully created
        if not twitter_client:
            logger.error("Failed to create Twitter client.")
            publish_sns(message="Failed to create Twitter client.")
            return {
                "statusCode": 500,
                "body": "Failed to create Twitter client.",
            }

        # Log the attempt to post the tweet
        logger.info(f"Attempting to send tweet with content: {tweet_content}")

        # Use the Twitter client to post the tweet
        response = twitter_client.create_tweet(text=tweet_content)

    # Handle general exceptions
    except Exception as e:
        logger.error(f"An unknown error occurred while attempting to post tweet: {e}")
        publish_sns(
            message=f"An unknown error occurred while attempting to post tweet: {e}"
        )
        return {
            "statusCode": 500,
            "body": f"An unknown error occurred while attempting to post tweet: {e}",
        }
    else:
        # Check if the tweet was successfully posted
        if response:
            logger.info(f"Tweet posted successfully! Tweet ID: {response}")
        else:
            logger.warning("Tweet was not posted, and no error was raised.")
            publish_sns(message="Tweet was not posted, and no error was raised.")


# AWS Lambda handler function
def lambda_handler(event, context):
    try:
        # Log that the Lambda function has started
        logger.info(f"Lambda function initiated.")

        # Retrieve API tokens and other parameters
        logger.info("Retrieving API tokens and parameters.")
        MEDIUM_API_TOKEN = get_param(param_name="medium_api_token")
        MEDIUM_USER_ID = get_param(param_name="medium_user_id")
        # LINKEDIN_ACCESS_TOKEN = get_param(param_name="linkedin_access_token")

        # Retrieve the list of AWS services
        service_list = get_services()
        service = random.choice(service_list)

        # Check if service list retrieval was successful
        if service_list is None:
            logger.error("Error retrieving services from AWS.")
            return {
                "statusCode": 500,
                "body": "Internal Server Error: Error retrieving services from AWS.",
            }

        # Generate an article about a randomly chosen service
        article_content = generate_article(service=service)

        # Check if article generation was successful
        if article_content is None:
            logger.error("Failed to generate article from open ai.")
            return {
                "statusCode": 500,
                "body": "Internal Server Error: Failed to generate article from open ai.",
            }

        # Parse the article content to get its title
        parser = MyHTMLParser()
        parser.feed(article_content)
        title = parser.title

        # Publish the article on Medium
        article_url = publish_article(
            title=title,
            content=article_content,
            medium_api_token=MEDIUM_API_TOKEN,
            medium_user_id=MEDIUM_USER_ID,
        )

        # Check if article publishing was successful
        if article_url is None:
            logger.error("Failed to publish article on Medium.")
            return {
                "statusCode": 500,
                "body": "Internal Server Error: Failed to publish article on Medium.",
            }

        # article_url = "https://medium.com/@cullancarey/introducing-aws-apprunner-a-powerful-managed-service-for-application-deployment-be56f8263545"

        # Prepare the LinkedIn post content
        # post_content = generate_linkedin_post_content(service=service)

        # Check if LinkedIn post content generation was successful
        # if post_content is None:
        #     logger.error("Failed to generate LinkedIn post content from open ai.")
        #     return {
        #         "statusCode": 500,
        #         "body": "Internal Server Error: Failed to generate LinkedIn post content from open ai.",
        #     }
        # logger.debug(post_content)

        # Share the article on LinkedIn
        # share_on_linkedin(
        #     article_url=article_url,
        #     title=title,
        #     linkedin_access_token=LINKEDIN_ACCESS_TOKEN,
        #     post_content=post_content,
        # )

        # Post a tweet with the article link
        tweet_content = f"Check out my latest blog on Medium about '{service}', all written by ChatGPT! #AWS #CloudComputing #OpenAI #GPT3 #Medium #ArtificialIntelligence #LinkedIn #Python #Boto3 #Automation #Programming #DevOps #Serverless #NLP #MachineLearning"
        # post_tweet(tweet_content=f"{tweet_content}\n{article_url}")

    # Handle unexpected exceptions
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        publish_sns(message=f"Error occurred in ArticlePublisher: {e}")
        return {"statusCode": 500, "body": f"Internal Server Error: {e}"}

    # Log the successful completion of the Lambda function
    logger.info("Lambda function completed successfully.")
    publish_sns(message=f"Successfully published article: {article_url}")
    return {
        "statusCode": 200,
        "body": "Successfully published article and shared on social media.",
    }


# lambda_handler(event=None, context=None)
