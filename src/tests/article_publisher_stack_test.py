from aws_cdk import App
from aws_cdk.assertions import Template

from stacks.article_publisher_stack import ArticlePublisherStack


def test_article_publisher_stack(snapshot):
    app = App()
    stack = ArticlePublisherStack(scope=app, id="TestArticlePublisherStack")

    template = Template.from_stack(stack)
    assert template.to_json() == snapshot
