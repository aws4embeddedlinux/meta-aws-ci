---
title: "2 – Build images in a fast and repeatable way"
weight: 10
---

### Introduction

In this module we use AWS CloudFormation, AWS CodePipelines and the Yocto project to define and deploy a solution that constructs a Linux image compatible with a Raspberry Pi 4.

Here is a high-level diagram of how the solution works and the services used:

![Solution Architecture](/images/02_build_images_solution_architecture.png)

### Prerequisites
- An AWS Account
- A Dockerhub Account
- Experience building images using Yocto
- Familiarity AWS CloudFormation, the AWS CLI and shell scripts
- (Optional) A Raspberry Pi 4 and an SD card to test the produced image

### Expected Environment 
If you are continuing from Module 1, you can continue to use Cloud9. Otherwise you can use AWS CloudShell which is a browser-based shell that makes it easy to securely manage, explore, and interact with your AWS resources. CloudShell is pre-authenticated with your console credentials. Common development and operations tools are pre-installed, so no local installation or configuration is required.


### Step 1 - Setup your environment

Open the AWS CloudShell service and run the following command to clone this repository and set `$PREFIX` to something unique like "mod2-YOUR_AWS_ACCOUNT_NUMBER".

```bash
cd ~/
git clone https://github.com/aws/meta-aws-ci
cd ~/meta-aws-ci/core/scripts/

export PREFIX=mod2-<<YOUR_AWS_ACCOUNT_NUMBER>>
```

### Step 2 – Securely store your Dockerhub credentials

When building containers, you will need to setup a secret that contains your Dockerhub username and password in AWS Secrets Manager. This is used to authenticate the CodePipeline with Dockerhub and used when composing images.

In AWS CloudShell, run this script without arguments and enter your Dockerhub username and password.  It will create a Secrets Manager entry and return an ARN that you will use when doing setup for the container projects.

```bash
./setup_dockerhub_secret.sh $PREFIX
```
Once this process is complete, store the secret ARN in an environment variable for later use.

```bash
export SECRET_ARN=arn:aws:secretsmanager:eu-west-1:123456789123:secret:dockerhub_EXAMPLE
```

### Step 3 – Create the baseline components
Baseline components are required for all other automation areas.

In AWS CloudShell, run the script to create the network layer. The network layer is a Virtual Private Cloud (VPC) for AWS CodeBuild.

```bash
./setup_ci_network.sh $PREFIX
```

### Step 4 – Install the container build layer and invoke the build process

In AWS CloudShell, run the script to create the container build layer. This script installs an AWS CodeBuild project to construct a custom container that is used to build Linux compatible images for the reference distribution named ‘Poky’.

```bash
./setup_ci_container_poky.sh $PREFIX $SECRET_ARN
```

Once this process is complete, invoke the build process. The process takes about 15 minutes to complete. You can monitor it using the CLI or by logging into the [AWS CodeBuild console](https://console.aws.amazon.com/codesuite/codebuild/projects). Make sure you select the right region. 


```bash
aws codebuild start-build --project-name $PREFIX-el-ci-container-poky
```

Finally, find out the image URI and store it in an environment variable for later use. 

```bash
aws ecr describe-repositories  | jq -r .repositories[].repositoryUri
export CONTAINER_URI=123456789123.dkr.ecr.eu-west-1.amazonaws.com/yoctoproject/EXAMPLE/buildmachine-poky
```

**Note**: Your OS may not have 'jq' installed. You can install it by typing 'sudo yum install jq -y' or 'sudo apt-get install jq -y' depeding on your Linux distribution.


### Step 5 – Install the Linux build layer and invoke the build process

In AWS CloudShell, run the script to create the Linux build layer. This script installs an AWS CodeBuild project to construct the core-image-minimal image for the QEMU x86-64 MACHINE target that includes the AWS IoT Device Client.  The AWS CodeBuild project file for this project is in the [meta-aws-demos](https://github.com/aws-samples/meta-aws-demos) repository. It also creates a new S3 bucket to store images it creates.

```bash
export VENDOR=rpi_foundation
export BOARD=rpi4-64 
export DEMO=aws-iot-greengrass-v2 
export YOCTO_RELEASE=dunfell
export COMPUTE_TYPE=BUILD_GENERAL1_LARGE
./setup_build_demos_prod.sh $PREFIX $CONTAINER_URI $VENDOR $BOARD $DEMO $YOCTO_RELEASE $COMPUTE_TYPE
```
Once the process is complete, find out the name of the newly created S3 bucket and store in an environment variable for later use

```bash
aws s3 ls | grep $PREFIX-el-build- | awk '{print $3}'
export S3_BUCKET=EXAMPLE-el-build-rpi4-64-aws-iot-gre-buildbucket-EXAMPLE
```

Invoke the build process. The process takes about 90 minutes to complete using `BUILD_GENERAL1_LARGE`. You can monitor it using the CLI or by logging into the [AWS CodeBuild console](https://console.aws.amazon.com/codesuite/codebuild/projects). Make sure you select the right region. 

```bash
aws codebuild start-build --project-name $PREFIX-el-build-$BOARD-$DEMO-$YOCTO_RELEASE
```
Once the build process is complete you can review the contents of the S3 bucket

```bash
aws s3 ls $S3_BUCKET
```

### Step 6 (Optional) - Download the image from S3 and test it

Download the image using the CLI or the AWS console and then use your favorite software to write the downloaded image to the SD card. Make sure you choose the right device. This process will overwrite the card.

```bash
dd if=image.bin of=/dev/<YOUR_SD_CARD_DEVICE> bs=4M status=progress
```

