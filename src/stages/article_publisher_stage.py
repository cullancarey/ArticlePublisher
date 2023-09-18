from aws_cdk import Stage, App, Environment
from constructs import Construct

from stacks.article_publisher_stack import ArticlePublisherStack


class ArticlePublisherPipelineStage(Stage):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        ArticlePublisherStack(
            scope=self,
            id="ArticlePublisherStack",
            description="Stack to deploy the resources for my article publisher lambda",
        )
