# CI Setup
## This describes the meta-aws, meta-aws-demos CI setup - setup github runner on CodeBuild

```
git clone https://github.com/aws4embeddedlinux/aws4embeddedlinux-ci-examples.git
cd aws4embeddedlinux-ci-examples
npm install .
npm run build
export AWS_DEFAULT_REGION=us-west-2
```

(only in this region you will be able to see aws4embeddedlinux repos)

```
cdk bootstrap
cdk deploy EmbeddedLinuxCodeBuildProject --require-approval=never
```

## Login into CodeBuild
- clone CodeBuild project - meta-aws-demos, meta-aws

- Manage default source credential -> OAuth app -> CodeBuild managed token -> connect to GitHub -> confirm

> [!IMPORTANT]
> If you are not selecting OAuth app, you will not see aws4embeddedlinux repos!

```
Select "Primary source webhook events" -> "Webhook - optional" -> "Rebuild every time a code change is pushed to this repository"

Add "Filter group 1" -> "WORKFLOW_JOB_QUEUED"

In the GitHub workflow:
Modify the GitHub action runs-on: ${{ vars.CODEBUILD_RUNNER_NAME }}-${{ github.run_id }}-${{ github.run_attempt }} CODEBUILD_RUNNER_NAME should be codebuild-EmbeddedLinuxCodebuildProjeNAME with prefix codebuild-meta-aws-demos
```
