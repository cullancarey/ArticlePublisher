# Deploy CDK Stack to Production

This GitHub Actions workflow automates the deployment of an AWS CDK stack to a production environment. It is triggered when changes are pushed to the `develop` branch. The workflow sets up AWS credentials, installs dependencies, and deploys the CDK stack.

## Workflow Details

### Workflow Name: Deploy-CDK-Stack/Prod

- **Run Name**: Running ${{github.workflow}} off of ${{ github.ref_name }}

### Trigger

This workflow is triggered on pushes to the `develop` branch.

```yaml
on:
  push:
    branches:
      - develop
```

### Permissions

This workflow requires specific permissions:

- `id-token: write`: This is required for requesting the JWT.
- `contents: read`: This is required for actions/checkout.

### Jobs

#### Deploy

- **Name**: Deploy Production
- **Uses**: `./.github/workflows/deploy.yaml`
- **Environment**: production

## CDK Deployment Workflow

### Workflow Name: Deploy

This workflow is designed to be called by other workflows and is used for deploying to different environments. It sets up AWS credentials, installs dependencies, and deploys the CDK stack based on the specified environment.

### Trigger

This workflow is meant to be called by other workflows using the `workflow_call` event. It takes an `environment` input parameter.

```yaml
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
        description: "The GitHub environment to deploy against."
```

### Permissions

This workflow also requires specific permissions:

- `id-token: write`: Required for requesting the JWT.
- `contents: read`: Required for actions/checkout.

### Job Details

#### Deploy

- **Name**: Deploy to ${{ inputs.environment }}
- **Environment**: ${{ inputs.environment }}
- **Environment Variables**:
  - `ENVIRONMENT`: ${{ vars.ENVIRONMENT }}
  - `CDK_DEPLOY_ACCOUNT`: ${{ vars.ACCOUNT_ID }}
  - `CDK_DEPLOY_REGION`: ${{ vars.REGION }}
- **Runs On**: ubuntu-latest
- **Defaults**:
  - Working Directory: `src`

#### Steps

1. **Checkout Repository**: This step checks out the repository to the GitHub Actions runner.

   ```yaml
   - name: Checkout
     uses: actions/checkout@v3
   ```

2. **Configure AWS Credentials**: This step configures AWS credentials for the specified environment.

   ```yaml
   - name: Configure AWS Credentials ${{ inputs.environment }}
     uses: aws-actions/configure-aws-credentials@v2
     with:
       role-to-assume: arn:aws:iam::${{ vars.ACCOUNT_ID }}:role/${{ vars.DEPLOYMENT_ROLE}}
       role-session-name: cdk-deployment-${{ vars.REGION }}-${{ vars.ACCOUNT_ID }}
       aws-region: ${{ vars.REGION }}
   ```

3. **Install Dependencies**: This step installs necessary dependencies, including AWS CDK and Python requirements.

   ```yaml
   - name: Install Dependencies
     run: |
       npm install -g aws-cdk
       pip install -r requirements.txt
   ```

4. **CDK Synth**: This step runs `cdk synth` to generate CloudFormation templates.

   ```yaml
   - name: CDK Synth
     run: |
       cdk synth
   ```

5. **Deploy CDK Stack**: This step deploys the CDK stack using `cdk deploy` with no approval required.

   ```yaml
   - name: Deploy Article Publisher
     run: |
       cdk deploy --app 'cdk.out/' --all --require-approval never
   ```
