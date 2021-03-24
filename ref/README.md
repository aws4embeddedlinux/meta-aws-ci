## Reference Implementation



# AWS services in use

- CodeBuild
- Elastic Container Registry
- Elastic Container Service
- S3
- Elastic File System
- Secrets Manager

# External AWS services in use

- **Github**.  You will need a Github account to implement this process.
- **Dockerhub**.  You will need a Dockerhub account to implement this
  process.

# Foundations

This project uses Continuous Integration tools from Amazon Web
Services. The tools operate containers in the context of a private
subnet where VPC routing rules control traffic to the internet. The
Cloudformation script for the nextwork is defined by the file
`cloudformation/ci_network.yml`.

**Warning** the script creates two Elastic IP instances which have
fixed cost.

1. Login to the AWS Console and navigate to your desired region.
2. Create a new stack using the stack template
`cloudformation/ci_network.yml`.
3. Note the following stack creation values of these propoerties in
   the **Outputs** tab of the stack creation job since they will need
   to be used in any further build project instantiation.
   - PrivateSubnet1
   - PrivateSubnet2
   - VPC

# Seeding the build machine

  High level process:

  1. Create and store a Github Personal Access Token for automated
     Github access and note the ARN.
  2. Create and store a Secrets Manager secret for your Dockerhub
     account and note the ARN.
  3. Run the CodeBuild project to build and store the build machine
     image in an Elastic Containter Registry private repository.

## Create the Github Personal Access Token

Follow the process in the AWS CodeBuild documentation that explains
the process very well. Note that, at the time of writing, you cannot
add the personal access token through the AWS Console. You must have
the AWS CLI installed.

## 

# Continuous Integration

Provides an AWS cloud native and serverless continuous integration
framework that facilitates build-stage-test.

# Pull request verification checks

Provides an AWS cloud native integration hook with the meta-aws Github
repo, providing bitbake layer integrity and verification checks. This
might be extended to incremental build-stage-test in the future.

# Device Tester integration

Device Tester provides automated testing and certification through
managed integration testing. meta-aws-ci provides the mechanisms to
coordinate edge devices under test with the harness running in the AWS
cloud.
