---
title: "2 – Build images in a fast and repeatable way"
weight: 10
---

### Introduction

In this module we use the AWS Cloud Development Kit (CDK), CDK Pipelines and the Yocto project to define and deploy a pipeline that hosts a self-updating application that constructs a Linux image compatible with a Raspberry Pi 4.

Here is a high-level diagram of how the solution works and the services used:
![Solution Architecture](/images/02_build_images_solution_architecture.png)

### Prerequisites
- An AWS Account
- Experience building images locally using Yocto
- Familiarity with the AWS Cloud Development Kit (CDK) or AWS CloudFormation
- Understanding of Continuous Delivery and Continuous Integration (CI/CD) concepts
- Experience writing code using TypeScript, Node.js or JavaScript
- (Optional) A Raspberry Pi 4 and an SD card to test the produced image

### What is the AWS Cloud Development Kit (CDK)?

The AWS Cloud Development Kit (CDK) is a framework for defining cloud infrastructure in code and provisioning it through AWS CloudFormation. AWS CDK enables you to build your cloud application without leaving your IDE. You can write your runtime code and define your AWS resources with the same programming language. We will be using Typescript in this Module.

{{% notice info %}}
If you have not used AWS CDK before, please consider working through the [Getting Started](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) section of the AWS CDK Developer Guide before continuing with this lab.
{{% /notice %}}

### What are CDK Pipelines? 

CDK Pipelines is a high-level construct library that makes it easy to set up a continuous deployment pipeline for your CDK applications, powered by AWS CodePipeline. Whenever you check your AWS CDK application's source code in to AWS CodeCommit, GitHub, or BitBucket, CDK Pipelines can automatically build, test, and deploy your new version. CDK Pipelines are self-updating; if you add new application stages or new stacks, the pipeline automatically reconfigures itself to deploy those new stages and/or stacks.


{{% notice info %}}
If you have not used CDK Pipelines before, please consider working through the code example [Continuous integration and delivery (CI/CD) using CDK Pipelines](https://docs.aws.amazon.com/cdk/latest/guide/cdk_pipeline.html) available in the AWS CDK Developer Guide before continuing with this lab. 
{{% /notice %}}

### Expected Environment 
- NodeJS, the latest LTS version is recommended
- NPM version 7 or later. View NPM upgrade instructions

### Step 1 - Fork the reference implementation for continuous integration for meta-aws

The meta-aws-ci project was built to provide mechanisms for meta-aws and meta-aws-demos continuous integration and pull request verification. It can also be used to provide mechanisms for OEM/ODM customers wanting to streamline Embedded Linux delivery. In addition, it provides a reference implementation that illustrates how to integrate and maintain AWS device software throughout the IoT product lifecycle.

{{% notice info %}}
You must have a GitHub account to fork an existing repo. If you do not have an account create one by following these instructions: [here](https://docs.github.com/en/get-started/signing-up-for-github/signing-up-for-a-new-github-account)
{{% /notice %}}

1. Using your web browser navigate to the [aws/meta-aws-ci](https://github.com/aws/meta-aws-ci) repository.

2. Click __Fork__ button in the top-right corner of the page and choose your user name

### Step 2 - Store GitHub and Docker Hub secrets securely in your account

1. A GitHub token is used to by the pipeline Stack and the image builder when interacting with GitHub. On your GitHub account, go to __Settings → Developer Settings → Personal access tokens__ and generate a new token. The token should have the __workflow__ scope selected

![GitHub personal access tokens](/images/02_build_images_github_personal_token.png)

2. Create a new secret by going to __AWS Console → AWS Secrets Manager__ and click on __Store a new secret__ then choose __Other type of secrets__, click on the __Plaintext__ tab and copy/paste your GitHub personal token in the text box. This secret needs to be named `github_personal_token`

![GitHub personal access tokens](/images/02_build_images_secrets_github.png) 

3. DockerHub credentials are used by the image builder when pulling upstream images from Docker Hub. Create a new secret by going to __AWS Console → AWS Secrets Manager__ and click on __Store a new secret__. Choose __Other type of secrets__, click on the __Secret key/value__ tab and create a `username` and `password` key/value pair. This secret needs to be named `dh` 

![GitHub personal access tokens](/images/02_build_images_secrets_dockerhub.png) 

### Step 3 - Compile and deploy the CDK project

1. Clone your forked project

```bash
git clone git@github.com:<YOUR_GITHUB_USER>/meta-aws-ci.git
```

2. Open the file `prerequisites-stack.ts` which is located under `cdk/lib` directory and change the variable `GithubCdkRepositoryOwner` and `GithubBaseImageRepositoryOwner` to match to your GitHub user name.

3. Navigate to the repository directory and commit your changes

```bash
cd meta-aws-ci
git add --all
git commit -m git commit -m "updated owners"
git push
```

4. Navigate to the __cdk__ directory and install the project dependencies

```bash
cd cdk
npm install
```

6. Ensure CDK builds correctly 

```bash
cdk synth
```

7. Setup temporary credentials. Make sure you have enough permissions.

```bash
export AWS_ACCESS_KEY_ID=ASIA3MLQD3T3MEXAMPLE
export AWS_SECRET_ACCESS_KEY=D8uy7l7koV3cDR8rYgtDVN0qJvSHrTKfgEXAMPLE
export AWS_SESSION_TOKEN=IQoJb3JpZ2luX2VjEI7//////////wEaCXVzLWVhc3QtMSJHMEUCIFfRRvaFjczQlyqgSvSzYMfviRvQjdFNFudh0gBooEAEXAMPLE
```

7. Bootstrap the AWS Account & region you are planning to use. This only needs to be done once per account-region combination.

```bash
export CDK_NEW_BOOTSTRAP=1 
export ACCOUNTID=<YOUR_ACCOUNT_ID>
export REGION=<YOUR_REGION>
cdk bootstrap \
    --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess \
    aws://$ACCOUNTID/$REGION
```

7. Deploy the project

```bash
cdk deploy
```
### Step 4 - Monitor the deployment process

The first thing that happens when you run ‘cdk deploy’ is that the CDK Pipelines project gets synthesized into a CloudFormation template. Then, this template gets deployed in your account.

CDK Pipelines project creates a CodePipeline pipeline called ‘DeviceImageBuilderPipeline’ in your account. This pipeline publishes a set of CloudFormation templates that define two application stacks. 

The first stack is called the ‘YoctoBaseImageBuilderStack’ and it is responsible for creating a Docker image that contains all the packages that Poky needs to be able to build images. The Docker image produced is stored in the AWS Elastic Container Registry (ECR). This takes approximately 15 minutes to build.

The second stack is called the ‘YoctoRaspberryPiImageBuilderStack’. This stack pulls the Docker image produced by in by the first stack and start building a Linux image using Poky. The image built in this module comes from a recipe available in the meta-aws-demos repository. The recipe targets a Raspberry Pi 4 and builds a basic operating system with support for filesystem, python, networking, and AWS IoT Greengrasss Version 2. This process takes approximately 90 minutes to build the first time but because the stack leverages from Amazon EFS to maintain the SSTATE cache, subsequent builds are much faster.

{{% notice note %}}
For more information about the image that this module builds, please explore the recipe here: 
https://github.com/aws-samples/meta-aws-demos/blob/master/raspberrypi4-64/aws-iot-greengrass-v2/
{{% /notice %}}

#### Troubleshooting deployment issues

- __You are not authorized to perform this operation__: You may need to manually add the permission "ec2:DescribeAvailabilityZones" to the " IAM role that starts with 'GreengrassDeviceImageBuil-PipelineBuildSynthCdk' if the pipeline 'DeviceImageBuilderPipeline' fails during the build stage because of the error "[Error at /GreengrassDeviceImageBuilder-PipelineStack/Testing/PrerequisitesStack] You are not authorized to perform this operation". This is due to a [bug](https://github.com/aws/aws-cdk/issues/2643) with CDK and new accounts. Once you have added the permission, you must retry the build process by clicking the "Retry" button on the console.

Example: In-line policy applied to IAM role 'GreengrassDeviceImageBuil-PipelineBuildSynthCdk...'
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "ec2:DescribeAvailabilityZones",
            "Resource": "*"
        }
    ]
}
```
- __Access Denied (Service: Amazon S3; Status Code: 403; Error Code: AccessDenied..)__: By default the reference implementation uses the caret symbol (^) which indicates “Compatible with version”. This means that NPM will update you to all future minor/patch versions, without incrementing the major version. Forcing packages.json to use a specific version of the AWS CDK like "1.111.0" may help resolving this issue if you encounter it. You will need to update NPM by running `npm update --force`.

Example: Setting dependencies to use a specific version - 'cdk/packages.json'
```json
{
  ...
  "dependencies": {
    "@aws-cdk/aws-codebuild": "1.111.0",
    "@aws-cdk/aws-codecommit": "1.111.0",
    "@aws-cdk/aws-codepipeline": "1.111.0",
    "@aws-cdk/aws-codepipeline-actions": "1.111.0",
    "@aws-cdk/aws-efs": "1.111.0",
    "@aws-cdk/aws-iam": "1.111.0",
    "@aws-cdk/aws-s3": "1.111.0",
    "@aws-cdk/core": "1.111.0",
    "@aws-cdk/pipelines": "1.111.0",
    "source-map-support": "^0.5.16"
  }
  ...
}

```
- __Error calling startBuild: Cannot have more than 0 builds in queue for the account__: Your account may be having a limit on the number of running On-Demand Instances. The reference implementation uses the largest instance available (145 GB , 72 vCPUs). Using a smaller instance should allow you to build the project if you encounter this error. You can change this setting from the console or by modifying the instance type defined in the file 'yocto-image-builder-stack.ts' from 'codebuild.ComputeType.X2_LARGE' to `codebuild.ComputeType.LARGE` or smaller. By default, the timeout is 1 hour, you may want to set it to a higher number as the 1st time build can take more than 1 hour in smaller instances.

Example: Modifying the project to use a different instance size and setting the timeout value - 'cdk/lib/stacks/yocto-image-builder-stack.ts'
```js
...
import { Construct, SecretValue, Stack, StackProps, RemovalPolicy, Duration } from '@aws-cdk/core';
...
const buildProject = new codebuild.PipelineProject(this, `YoctoBuild-${machineType}-${projectType}-${yoctoProjectRelease}`, {
   ...
    timeout: Duration.hours(8)
    ...
    environment: {
        ...
        computeType: codebuild.ComputeType.LARGE,
        ...
    },
   ...
});
```

### Step 5 (Optional) - Download the image from S3 and test it

1. Get the name of the S3 bucket that contains the image

```bash
BUCKET=$(aws s3 ls | grep 'images' | awk '{print $3}') 
```

2. Download the image to your local environment

```bash
PREFIX=dunfell/raspberrypi4-64/aws-iot-greengrass-v2//build-output/deploy/images/raspberrypi4-64
FILE=core-image-minimal-raspberrypi4-64.rpi-sdimg
aws s3 cp s3://$BUCKET/$PREFIX/$FILE .
```

3. Use your favorite software to write the downloaded image to an sd card.

{{% notice warning %}}
Make sure you choose the right device. This process will overwrite the card.
{{% /notice %}}

```bash
dd if=$FILE of=/dev/<YOUR_SD_CARD_DEVICE> bs=4M status=progress
```
