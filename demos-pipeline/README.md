# Welcome to your CDK TypeScript project

This is a CDK development with TypeScript.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

-   `npm run build` compile typescript to js
-   `npm run watch` watch for changes and compile
-   `npm run test` perform the jest unit tests
-   `cdk deploy` deploy this stack to your default AWS account/region
-   `cdk diff` compare deployed stack with current state
-   `cdk synth` emits the synthesized CloudFormation template

Project Specific:
-   `npm run format` runs prettier and eslint on the repository
-   `npm run zip-data` bundles the files for creating build host containers
-   `npm run check` checks for lint and format issues

## Setting Up

1. Create a `CodeStar` `Connection` in your AWS account.
1. Put the ARN for this `Connection` in `bin/demos-pipeline.ts`
1. TODO: customizing the pipeline, creating a new one, etc.
1. Run the following:
```
npm install .
npm run build

cdk bootstrap

npm run zip-data
cdk deploy \
    BuildImageData \
    BuildImageRepo \
    DemoPipelineNetwork \
    BuildImagePipeline \
    DemosPipelineStack

```

Run the resulting `BuildImagePipeline` (e.g. `ubuntu_22_04BuildImagePipeline` when using Ubuntu 22.04) to create the build host.

After that completes, the DemoPipeline is ready to run.

## Stacks and Constructs

### Build Image Stacks

Used to create a build host container image.

#### BuildImageData

The assets required to create a build host container (Dockerfile, Buildspec, etc).

#### BuildImageRepo

The ECR repository to store build host container images in. To prevent data loss on a pipeline update and ease development, this stack is separated.

#### BuildImagePipeline

A CodePipeline Pipeline which builds the host container images.

## Contributing

TODO: Notes contribution process (pre-commit, running tests, formatting and test standards, etc)
