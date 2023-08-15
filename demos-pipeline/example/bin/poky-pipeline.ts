#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import {
  DemoPipelineStack,
  RepoKind,
  BuildImageDataStack,
  BuildImagePipelineStack,
  BuildImageRepoStack,
  PipelineNetworkStack,
  ImageKind,
} from "aws4embeddedlinux-cdk-lib";

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
  terminationProtection: false, // TODO: enable.
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
const vpc = new PipelineNetworkStack(app, "PipelineNetwork", {
  ...defaultProps,
});

/**
 * Create a poky pipeline.
 */
new DemoPipelineStack(app, "PokyPipeline", {
  ...defaultProps,
  imageRepo: buildImageRepo.repository,
  imageTag: ImageKind.Ubuntu22_04,
  vpc: vpc.vpc,
});

/**
 * Create a meta-aws-demos pipeline for the Qemu example.
 */
new DemoPipelineStack(app, "QemuDemoPipeline", {
  ...defaultProps,
  imageRepo: buildImageRepo.repository,
  imageTag: ImageKind.Ubuntu22_04,
  vpc: vpc.vpc,
  layerKind: RepoKind.MetaAwsDemo,
  layerRepoName: "qemu-demo-layer-repo",
});

/**
 * Create a poky pipeline.
 */
// TODO(nateglims): implement
// new DemoPipelineStack(app, "three-p-Pipeline", {
//   ...defaultProps,
//   imageRepo: buildImageRepo.repository,
//   imageTag: ImageKind.Ubuntu22_04,
//   vpc: vpc.vpc,
// });
