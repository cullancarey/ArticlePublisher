from aws_cdk import pipelines, Stack, Aws, Environment, App
from constructs import Construct
from stages.article_publisher_stage import ArticlePublisherPipelineStage


class ArticlePublisherPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        pipeline = pipelines.CodePipeline(
            self,
            "ArticlePublisherPipeline",
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.git_hub(
                    repo_string="cullancarey/ArticlePublisher", branch="develop"
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "python -m pip install -r requirements.txt",
                    "cdk synth",
                ],
            ),
            docker_enabled_for_synth=True,
        )

        # Do this as many times as necessary with any account and region
        # Account and region may different from the pipeline's.
        pipeline.add_stage(ArticlePublisherPipelineStage(self, "Production"))
