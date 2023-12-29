from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    Duration,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as event_targets,
    aws_iam as iam,
    aws_sns as sns,
)
from constructs import Construct


class ArticlePublisherStack(Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # SNS topic to alert on lambda failures
        article_publisher_topic = sns.Topic(self, "ArticlePublisherTopic")

        # Create a subscription for the sns topic
        sns.Subscription(
            self,
            "ArticlePublisherTopicSubscription",
            topic=article_publisher_topic,
            endpoint="cullancarey@yahoo.com",
            protocol=sns.SubscriptionProtocol.EMAIL,
        )

        # Lambda Function (Assuming that this is previously created)
        article_publisher_lambda = _lambda.DockerImageFunction(
            self,
            f"ArticlePublisherLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                "assets/lambda/article_publisher/"
            ),
            timeout=Duration.seconds(300),
            architecture=_lambda.Architecture.X86_64,
            log_retention=logs.RetentionDays.ONE_YEAR,
        )

        # Add sns topic arn as lambda environment variable
        article_publisher_lambda.add_environment(
            "SNS_TOPIC_ARN", article_publisher_topic.topic_arn
        )

        # Define a policy statement
        statement = iam.PolicyStatement(
            sid="AllowSNS",
            actions=["sns:Publish"],
            resources=[article_publisher_topic.topic_arn],
            effect=iam.Effect.ALLOW,
        )

        # Add the policy statement to the Lambda function's execution role
        article_publisher_lambda.role.add_to_policy(statement)

        # Grant read access to the Lambda function for each SSM parameter

        _ = [
            ssm.StringParameter.from_secure_string_parameter_attributes(
                self, id=param, parameter_name=param
            ).grant_read(article_publisher_lambda)
            for param in [
                "medium_api_token",
                "medium_user_id",
                "openai_api_token",
                "linkedin_access_token",
                "cullan_twitter_api_key",
                "cullan_twitter_access_token",
                "cullan_twitter_access_secret_token",
                "cullan_twitter_secret_key",
            ]
        ]

        events.Rule(
            self,
            "ArticlePublisherLambdaRule",
            description=f"Rule to trigger {article_publisher_lambda.function_name}",
            schedule=events.Schedule.cron(
                week_day="2,4,5", hour="14", minute="0", month="*", year="*"
            ),
            targets=[event_targets.LambdaFunction(article_publisher_lambda)],
            enabled=False,
        ),
