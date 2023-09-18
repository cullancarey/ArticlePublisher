#!/usr/bin/env python3
"""Module import for cdk and other required packages"""
import os
from aws_cdk import App, Environment, Tags, Stack
from stacks.article_publisher_stack import ArticlePublisherStack


def add_tags(
    stack: Stack = None,
    app: App = None,
    default_tags: dict = None,
):
    if app:
        for k, v in default_tags.items():
            Tags.of(app).add(k, v)
    if stack:
        Tags.of(stack).add("stack_name", stack.stack_name)


app = App()


environment = os.environ.get("ENVIRONMENT")
# environment = "production"
environment_config = app.node.try_get_context(environment)
account_id = environment_config.get("account_id")
region = environment_config.get("region")


env = Environment(account=account_id, region=region)

# Default tags for all stacks
default_tags = {
    "environment": environment,
    "project": "ArticlePublisher",
    "owner": "Cullan Carey",
}

add_tags(app=app, default_tags=default_tags)

# Add the new pipeline stack
article_publisher_stack = ArticlePublisherStack(
    scope=app,
    id="ArticlePublisherStack",
    description="Stack to deploy the resources for my article publisher pipeline",
    env=env,
)
add_tags(article_publisher_stack)
app.synth()
