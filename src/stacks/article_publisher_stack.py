from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    Duration,
    aws_logs as logs,
    aws_events as events,
    aws_events_targets as event_targets,
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

        # Lambda Function (Assuming that this is previously created)
        article_publisher_lambda = _lambda.DockerImageFunction(
            self,
            f"ArticlePublisherLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                "assets/lambda/article_publisher/"
            ),
            timeout=Duration.seconds(120),
            architecture=_lambda.Architecture.X86_64,
            log_retention=logs.RetentionDays.ONE_YEAR,
        )

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
            ]
        ]

        events.Rule(
            self,
            "ArticlePublisherLambdaRule",
            description=f"Rule to trigger {article_publisher_lambda.function_name}",
            schedule=events.Schedule.cron(
                week_day="*", hour="14", minute="0", month="*", year="*"
            ),
            targets=[event_targets.LambdaFunction(article_publisher_lambda)],
        ),
