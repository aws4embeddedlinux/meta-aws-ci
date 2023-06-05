# Welcome to your CDK TypeScript project

This is a blank project for CDK development with TypeScript.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

-   `npm run build` compile typescript to js
-   `npm run watch` watch for changes and compile
-   `npm run test` perform the jest unit tests
-   `cdk deploy` deploy this stack to your default AWS account/region
-   `cdk diff` compare deployed stack with current state
-   `cdk synth` emits the synthesized CloudFormation template

-   `npm run format` runs prettier and eslint on the repository
-   `npm run zip-data` bundles the files for creating build host containers
-   `npm run check` checks for lint and format issues

## Setting Up

```
npm install .
npm run build

cdk bootstrap

npm run zip-data
cdk deploy ...Stacks...
```

## Stacks and Constructs

### Build Image Stacks

Used to create a build host container image.

#### BuildImageData

The assets required to create a build host container (Dockerfile, Buildspec, etc).

#### BuildImageRepo

The ECR repository to store build host container images in. To prevent data loss on a pipeline update and ease development, this stack is separated.

#### BuildImagePipeline

A CodePipeline Pipeline which builds the host container images.
