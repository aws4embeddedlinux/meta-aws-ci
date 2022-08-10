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
   git clone https://github.com/aws4embeddedlinux/meta-aws-ci
   cd ~/meta-aws-ci/core/scripts/
   export ACCOUNT_ID=123456789123
   export PREFIX=mod2-$ACCOUNT_ID
   ```
3. When building containers, you will need a secret setup in AWS Secret
Manager. Run this script and enter your Dockerhub username
and password.  It will create a Secrets Manager entry and return an
ARN that you will use when doing setup for the container projects.

   ```bash
   ./setup_dockerhub_secret.sh $PREFIX
   ```

4. Once this process is complete, store the secret ARN in an environment variable for later use.

   ```bash
   export SECRET_ARN=arn:aws:secretsmanager:eu-west-1:123456789123:secret:dockerhub_EXAMPLE
   ```

## Baseline components

Baseline components are required for all other automation areas.

1. In AWS CloudShell, run the script to create the network layer. The
   network layer is a Virtual Private Cloud (VPN) for AWS CodeBuild.

   ```bash
   ./setup_ci_network.sh $PREFIX
   ```

## Container components

1. Install the container build layer to your target.  The script
   naming convention is
   `setup_ci_container_<distro>[.<release>].sh`.

   In the Poky case, you install the container build using the script
   with the name `poky` in it.

   ```bash
   ./setup_ci_container_poky.sh $PREFIX $SECRET_ARN
   ```

    In the TI (Arago) case, you will need to be more specific.

   ```bash
   ./setup_ci_container_ti.dunfell.sh $PREFIX $SECRET_ARN
   ```

   If you have forked the meta-aws-ci repository and need to use the
   repo from your own context, set the `GITHUB_REPO` variable. For
   example:


   ```bash
   GITHUB_ORG=rpcme ./setup_ci_container_ti.dunfell.sh $PREFIX $SECRET_ARN
   ```
2. Once this process is complete, invoke the build process. The process takes about 15 minutes to complete. You can monitor it using the CLI or by logging into the AWS CodeBuild console. Make sure you select the right region.

   ```bash
   aws codebuild start-build --project-name $PREFIX-el-ci-container-poky
   ```

3. Finally, find out the image URI and store it in an environment variable for later use.

   ```bash
   aws ecr describe-repositories --query repositories[].repositoryUri --output text
   export CONTAINER_URI=123456789123.dkr.ecr.eu-west-1.amazonaws.com/yoctoproject/EXAMPLE/buildmachine-poky
   ```

## Embedded Linux build components

1. In AWS CloudShell, run the script to create the Linux build layer. This script installs an AWS CodeBuild project to construct the core-image-minimal image for the QEMU x86-64 MACHINE target that includes the AWS IoT Device Client. The AWS CodeBuild project file for this project is in the
   [meta-aws-demos](https://github.com/aws-samples/meta-aws-demos) It also creates a new S3 bucket to store images it creates.

   ```bash
   export VENDOR=rpi_foundation
   export BOARD=rpi4-64
   export DEMO=aws-iot-greengrass-v2
   export YOCTO_RELEASE=dunfell
   export COMPUTE_TYPE=BUILD_GENERAL1_LARGE
   ./setup_build_demos_prod.sh $PREFIX $CONTAINER_URI $VENDOR $BOARD $DEMO $YOCTO_RELEASE $COMPUTE_TYPE
   ```

   If you are setting up this for a repo not in aws-samples, then you
   can override the organization where your meta-aws-demos repo is running.

   ```bash
   GITHUB_ORG=rpcme ./setup_build_demos_prod.sh $PREFIX $CONTAINER_URI $VENDOR $BOARD $DEMO $YOCTO_RELEASE $COMPUTE_TYPE
   ```

2. Once the process complete, find out the name of the newly created S3 bucket and store in an environment variable for later use

   ```bash
   aws s3 ls | grep $PREFIX-el-build- | awk '{print $3}'
   export S3_BUCKET=EXAMPLE-el-build-rpi4-64-aws-iot-gre-buildbucket-EXAMPLE
   ```

3. Invoke the build process. You can monitor it using the CLI or by logging into the AWS CodeBuild console. Make sure you select the right region.

   ```bash
   aws codebuild start-build --project-name $PREFIX-el-build-$BOARD-$DEMO-$YOCTO_RELEASE
   ```

4. Once the build process is complete you can review the contents of the S3 bucket
   ```bash
   aws s3 ls $S3_BUCKET --recursive
   ```
