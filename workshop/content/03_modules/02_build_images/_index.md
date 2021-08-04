---
title: "2 – Build images in a fast and repeatable way"
weight: 10
---

In this module we use the AWS Cloud Development Kit (CDK) to define and deploy a pipeline that hosts an application. The application is designed to build Yocto images in a fast and repeatable way. 

![Solution Architecture](/images/02_build_images_solution_architecture.png)

### What is the AWS Cloud Development Kit (CDK)?

The AWS Cloud Development Kit (CDK) is a framework for defining cloud infrastructure in code and provisioning it through AWS CloudFormation. The AWS CDK lets you define applications in the AWS Cloud using your programming language of choice.  We will be using Typescript in this Module.

### What are CDK Pipelines? 

CDK Pipelines is a construct library module for continuous delivery of AWS CDK applications. Whenever you check your AWS CDK app's source code in to AWS CodeCommit, GitHub, or BitBucket, CDK Pipelines can automatically build, test, and deploy your new version. CDK Pipelines are self-updating; if you add new application stages or new stacks, the pipeline automatically reconfigures itself to deploy those new stages and/or stacks.


{{% notice note %}}
CDK Pipelines is currently in developer preview, and its API is subject to change. Breaking API changes will be announced in the AWS CDK Release Notes. https://github.com/aws/aws-cdk/releases
{{% /notice %}}


### Step 1 - Fork the reference implementation for continuous integration for meta-aws

The meta-aws-ci project was built to provide mechanisms for meta-aws and meta-aws-demos continuous integration and pull request verification. It can also be used to provide mechanisms for OEM/ODM customers wanting to streamline Embedded Linux delivery. In addition, it provides a reference implementation that illustrates how to integrate and maintain AWS device software throughout the IoT product lifecycle.

{{% notice info %}}
You must have a GitHub account to fork an existing repo. If you do not have an account create one by following these instructions: [here](https://docs.github.com/en/get-started/signing-up-for-github/signing-up-for-a-new-github-account)
{{% /notice %}}

1. Using your web browser navigate to the [aws/meta-aws-ci](https://github.com/aws/meta-aws-ci) repository.

2. Click __Fork__ button in the top-right corner of the page and choose your user name

### Step 2 - Store GitHub and Docker Hub secrets securely in your account

1. A Github token is used to by the pipeline Stack and the imaage builder when interacting with Github. On your Github account, go to __Settings → Developer Settings → Personal access tokens__ and generate a new token. The token should have __workflow__ scope selected

![GitHub personal access tokens](/images/02_build_images_github_personal_token.png)

2. Create a new secret by going to __AWS Console → AWS Secrets Manager__ and click on __Store a new secret__ then choose __Other type of secrets__, click on the __Plaintext__ tab and copy/paste your GitHub personal token in the text box. This secret needs to be named `github_personal_token`

![GitHub personal access tokens](/images/02_build_images_secrets_github.png) 

3. DockerHub credentials are used by the image builder when pulling upstream images from Docker Hub. Create a new secret by going to __AWS Console → AWS Secrets Manager__ and click on __Store a new secret__ then choose __Other type of secrets__, click on the __Secret key/value__ tab and create a `username` and `password` key/value pair. This secret needs to be named `dh` 

![GitHub personal access tokens](/images/02_build_images_secrets_dockerhub.png) 

### Step 3 - Compile and deploy the CDK project

1. Clone your forked project

```bash
git clone git@github.com:<<YOUR_GITHUB_USER>>/meta-aws-ci.git
```

2. Navigate to the __cdk__ directory and install the project dependencies

```bash
cd meta-aws-ci/cdk
npm update
```

3. Deploy the project
```bash
cdk deploy
```
### Step 4 - Monitor the deployment process

The first thing that happens when you run ‘cdk deploy’ is that the CDK Pipelines project gets synthesized into a CloudFormation template. Then, this template gets deployed in your account.

CDK Pipelines project creates a CodePipeline pipeline called ‘DeviceImageBuilderPipeline’ in your account. This pipeline publishes a set of CloudFormation templates that define two application stacks. 

The first stack is called the ‘YoctoBaseImageBuilderStack’ and it is responsible for creating a Docker image that contains all the packages that Poky needs to be able to build images. The Docker image produced is stored in the AWS Elastic Container Registry (ECR).

The second stack is called the ‘YoctoRaspberryPiImageBuilderStack’. This stack pulls the Docker image produced by in by the first stack and start building a Linux image using Poky. The image built in this module comes from a recipe available in the meta-aws-demos repository. The recipe targets a RaspberryPi 4. It builds a basic operating system with support for filesystem, python, networking, and AWS IoT GreenGrasss.


{{% notice note %}}
For more information about the image that this module builds, please explore the recipe here: 
https://github.com/aws-samples/meta-aws-demos/blob/master/raspberrypi4-64/aws-iot-greengrass-v2/
{{% /notice %}}

### Step 5 - Download the image from S3 and test it

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
dd if=$FILE of=/dev/<<YOUR_SD_CARD_DEVICE>> bs=4M status=progress
```
