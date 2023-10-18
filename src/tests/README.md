# AWS CDK Snapshot Testing with Syrupy

This README describes how to perform snapshot testing on an AWS Cloud Development Kit (CDK) stack using the Syrupy package.

## Prerequisites

Before running the test, make sure you have the following:

1. Python 3.x
2. AWS CDK CLI installed
3. Syrupy and pytest installed. If not, you can install them using pip:

    ```bash
    pip install syrupy pytest
    ```

## Snapshot Testing

Snapshot testing is a feature that ensures your application's UI does not change unexpectedly. It takes a "snapshot" of a rendered UI component and saves it to a file. On subsequent test runs, the rendered output is compared to the saved snapshot. If they differ, either the change is unexpected, or the snapshot needs to be updated to the new version of the UI component.

## Syrupy

Syrupy is a pytest snapshot plugin. It is used to capture snapshots of test expectations and compare them against actual outcomes. Syrupy is especially useful for complex objects that are tedious to match manually.

## The Test Code

The test code is straightforward:

```python
from aws_cdk import App
from aws_cdk.assertions import Template

from stacks.article_publisher_stack import ArticlePublisherStack

def test_article_publisher_stack(snapshot):
    app = App()
    stack = ArticlePublisherStack(scope=app, id="TestArticlePublisherStack")

    template = Template.from_stack(stack)
    assert template.to_json() == snapshot
```

### Explaining the Code

- Import AWS CDK `App` and `Template` for setting up the stack and extracting its CloudFormation template respectively.
- Import the stack (`ArticlePublisherStack`) you want to test.
- Define a test function `test_article_publisher_stack` that accepts a `snapshot` argument.
- Create an instance of the stack.
- Extract the CloudFormation template.
- Compare the extracted template JSON with the snapshot.

## Running the Test

To run the snapshot test, execute the following command:

```bash
pytest --snapshot-update
```

This will update the snapshot on the first run. On subsequent runs, it will use this snapshot to compare with the current CloudFormation template of the stack.

If the stack changes, and the change is expected, you can update the snapshot by running the same command again.

## Additional Notes

- Ensure that you're running the command in the appropriate virtual environment, if you're using one.
- If you're encountering any argument conflicts like `--snapshot-update: conflicting option string: --snapshot-update`, make sure to check the pytest plugins installed and loaded.

That's it! You now have a snapshot test for your AWS CDK stack using Syrupy.