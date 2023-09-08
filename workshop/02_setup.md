---
title: "Setup"
weight: 20
---
In this section, learners will invoke mechanisms to setup artifacts for the modules although some artifacts may be setup by the workshop harness. The section will walk the learner through all the created artifacts and tools so a baseline understanding of the toolchain can be set prior to progressing to Module 1

## Launch Workshop Resources with CloudFormation
Before starting the Embedded Linux workshop, you need to create the required AWS resources. To do this, we provide an AWS CloudFormation template to create a stack that contains the resources. When you create the stack, 
AWS creates a number of resources in your account. 

<a id="Launch_Workshop_Resources_with_CloudFormation"></a>

Choose an AWS region from the below list where you want to launch your CloudFormation stack. It is recommended to choose the closest region. The required AWS resource for the workshop are provisioned with AWS CloudFormation. Simply click the AWS region where you want to launch your stack. 

By choosing one of the links below you will be automatically redirected to the CloudFormation section of the AWS Console where your stack will be launched.
* [Launch CloudFormation stack in eu-central-1](https://console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/create/review?templateURL=https://aws-iot-workshop-artifacts.s3.amazonaws.com/4f74bcdb2e45dbf5/2021-07-29/cfn/cfn-iot-c9-v2-generic.json&stackName=EmbeddedLinux&param_C9InstanceType=c5.9xlarge&param_C9UserDataScript=c9-ub1804-embeddedlinux.sh&param_C9ImageId=ubuntu-18.04-x86_64) (Frankfurt)
* [Launch CloudFormation stack in eu-west-1](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/create/review?templateURL=https://aws-iot-workshop-artifacts.s3.amazonaws.com/4f74bcdb2e45dbf5/2021-07-29/cfn/cfn-iot-c9-v2-generic.json&stackName=EmbeddedLinux&param_C9InstanceType=c5.9xlarge&param_C9UserDataScript=c9-ub1804-embeddedlinux.sh&param_C9ImageId=ubuntu-18.04-x86_64) (Ireland)
* [Launch CloudFormation stack in us-east-1](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/create/review?templateURL=https://aws-iot-workshop-artifacts.s3.amazonaws.com/4f74bcdb2e45dbf5/2021-07-29/cfn/cfn-iot-c9-v2-generic.json&stackName=EmbeddedLinux&param_C9InstanceType=c5.9xlarge&param_C9UserDataScript=c9-ub1804-embeddedlinux.sh&param_C9ImageId=ubuntu-18.04-x86_64) (N. Virginia)
* [Launch CloudFormation stack in us-west-2](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/create/review?templateURL=https://aws-iot-workshop-artifacts.s3.amazonaws.com/4f74bcdb2e45dbf5/2021-07-29/cfn/cfn-iot-c9-v2-generic.json&stackName=EmbeddedLinux&param_C9InstanceType=c5.9xlarge&param_C9UserDataScript=c9-ub1804-embeddedlinux.sh&param_C9ImageId=ubuntu-18.04-x86_64) (Oregon)
* [Launch CloudFormation stack in ap-southeast-1](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks/create/review?templateURL=https://aws-iot-workshop-artifacts.s3.amazonaws.com/4f74bcdb2e45dbf5/2021-07-29/cfn/cfn-iot-c9-v2-generic.json&stackName=EmbeddedLinux&param_C9InstanceType=c5.9xlarge&param_C9UserDataScript=c9-ub1804-embeddedlinux.sh&param_C9ImageId=ubuntu-18.04-x86_64) (Singapore)
* [Launch CloudFormation stack in ap-southeast-2](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-2#/stacks/create/review?templateURL=https://aws-iot-workshop-artifacts.s3.amazonaws.com/4f74bcdb2e45dbf5/2021-07-29/cfn/cfn-iot-c9-v2-generic.json&stackName=EmbeddedLinux&param_C9InstanceType=c5.9xlarge&param_C9UserDataScript=c9-ub1804-embeddedlinux.sh&param_C9ImageId=ubuntu-18.04-x86_64) (Sydney)


