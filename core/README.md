**under construction**


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

## Installing and running

With these steps, you will need to keep your region consistent.  The
actions will not work cross-region, such as installing the network to
us-east-1 and the container build to us-east-2.

1. Install the network layer to your target region.

   <a
href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=el_network&templateURL=https://raw.githubusercontent.com/aws/meta-aws-ci/master/core/cfn/ci_network.yml"><img
src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"></a>

2. Install the container build layer to your target. In this case, you
   install the container build for the reference distribution named **Poky**.

   <a
href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=el_image_poky&templateURL=https://raw.githubusercontent.com/aws/meta-aws-ci/master/core/cfn/ci_image_poky.yml"><img
src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"></a>

3. Invoke the container build.

4. Install the AWS CodeBuild project to construct the
   core-image-minimal image for the QEMU x86-64 MACHINE target that
   includes the AWS IoT Device Client.  The AWS CodeBuild project file for this
   project is in the
   (https://github.com/aws-samples/meta-aws-demos)[meta-aws-demos] repository.

   <a
href="https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=el_poky_x86-64_aws-iot-device-client&templateURL=https://raw.githubusercontent.com/aws/meta-aws-ci/master/core/cfn/ci_poky_x86-64_aws-iot-device-client.yml"><img
src="https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png"></a>
