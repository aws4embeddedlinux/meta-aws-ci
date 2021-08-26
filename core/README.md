<font color="red">**under construction**</font>

The **core** part of this repository contains the standard set of AWS
CloudFormation and other data for **meta-aws** Continuous Integration
and Continuous Delivery practices.  Customers can reuse these
artifacts to build Linux distributions with Yocto Project.

## How this is organized

   - **buildspec**: AWS CodeBuild files that are not meta-aws or
     meta-aws-demos specific.  For example, the buildspec file for
     building containers used in AWS CodeBuild.
   - **cfn**: AWS CloudFormation files that hydrate AWS cloud objects
     in your AWS account to perform Yocto Project builds and
     housekeeping activities.
   - **containers**: Container definitions for specific build
     activities.  For example, there is a container definitions for
     specific distributions like **Poky** (Yocto Project) and
     **Arago** (Texas Instruments).

## Working environment

For simplicity, we assume you are operating in an AWS CloudShell
context.  They will run on a Linux or Mac OS machine with AWS Command
Line Interface installed.  Run on a Windows machine at your own risk.

1. Login to the AWS Console.  Open the AWS CloudShell service and wait
   for the environment to run.
2. In AWS CloudShell, run the following command to clone this repository.

   ```bash
   git clone https://github.com/aws/meta-aws-ci
   ```

You will also need an Amazon S3 bucket.

1. In AWS CloudShell, run the script to create an Amazon S3
   bucket for AWS Cloudformation scripts.  You may run this script as
   many times as you wish to update the AWS CloudFormation files from
   this repository to the S3 bucket.
   
   **INFO**: this step creates an S3 bucket in your account and will
   copy files into the S3 bucket, possibly incurring storage charges.

   ```bash
   ~/meta-aws-ci/core/scripts/setup_s3_objects.sh
   ```

2. When building containers, you will need a secret setup in AWS Secret
Manager.  Run this script without arguments and enter your Dockerhub username
and password.  It will create a Secrets Manager entry and return an
ARN that you will use when doing setup for the container projects.

   ```bash
   ~/meta-aws-ci/core/scripts/setup_dockerhub_secret.sh
   ```

## Baseline components

Baseline components are required for all other automation areas.

1. In AWS CloudShell, run the script to create the network layer. The
   network layer is a Virtual Private Cloud (VPN) for AWS CodeBuild.

   ```bash
   ~/meta-aws-ci/core/scripts/setup_ci_network.sh
   ```

### Container components

1. Install the container build layer to your target. In this case, you
   install the container build for the reference distribution named **Poky**.

   ```bash
   ~/meta-aws-ci/core/scripts/setup_ci_container_poky.sh ${prefix} ${secret_arn}
   ```

3. Invoke the container build.

   ```bash
   aws codebuild start-build --project-name ${prefix}-el-ci-container-poky_YPBuildImage
   ```

### Embedded Linux build components

4. Install the AWS CodeBuild project to construct the
   core-image-minimal image for the QEMU x86-64 MACHINE target that
   includes the AWS IoT Device Client.  The AWS CodeBuild project file for this
   project is in the
   (https://github.com/aws-samples/meta-aws-demos)[meta-aws-demos] repository.

   ```bash
   ~/meta-aws-ci/core/scripts/setup_build_poky.sh ${prefix} ${machine} ${target}
   ```
