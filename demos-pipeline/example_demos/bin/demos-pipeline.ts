#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { DemoPipelineStack, DeviceKind } from "aws4embeddedlinux-cdk-lib";
import { BuildImageDataStack } from "aws4embeddedlinux-cdk-lib";
import { BuildImagePipelineStack, ImageKind } from "aws4embeddedlinux-cdk-lib";
import { BuildImageRepoStack } from "aws4embeddedlinux-cdk-lib";
import { PipelineNetworkStack } from "aws4embeddedlinux-cdk-lib";

const app = new cdk.App();

/**
 * User Data
 */
const env = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: process.env.CDK_DEFAULT_REGION,
};

/**
 * Use these default props to enable termination protection and tag related AWS
 * Resources for tracking purposes.
 */
const defaultProps: cdk.StackProps = {
  tags: { PURPOSE: "META-AWS-BUILD" },
  terminationProtection: false,
  env,
};

/**
 * Set up the Stacks that create our Build Host.
 */
const buildImageData = new BuildImageDataStack(app, "BuildImageData", {
  ...defaultProps,
  bucketName: `build-image-data-${env.account}-${env.region}`,
});

const buildImageRepo = new BuildImageRepoStack(app, "BuildImageRepo", {
  ...defaultProps,
});

new BuildImagePipelineStack(app, "BuildImagePipeline", {
  ...defaultProps,
  dataBucket: buildImageData.bucket,
  repository: buildImageRepo.repository,
  imageKind: ImageKind.Ubuntu22_04,
});

/**
 * Set up networking to allow us to securely attach EFS to our CodeBuild instances.
 */
const vpc = new PipelineNetworkStack(app, "DemoPipelineNetwork", {
  ...defaultProps,
});

/**
 * Create a Qemu Pipeline based on meta-aws-demos.
 */
new DemoPipelineStack(app, "QemuDemoPipeline", {
  ...defaultProps,
  imageRepo: buildImageRepo.repository,
  imageTag: ImageKind.Ubuntu22_04,
  device: DeviceKind.Qemu,
  vpc: vpc.vpc,
});

/**
 * Create a AGL NXP Pipeline based on meta-aws-demos.
 */
new DemoPipelineStack(app, "AglNxpPipeline", {
  ...defaultProps,
  imageRepo: buildImageRepo.repository,
  imageTag: ImageKind.Ubuntu22_04,
  device: DeviceKind.AglNxpGoldbox,
  vpc: vpc.vpc,
});
