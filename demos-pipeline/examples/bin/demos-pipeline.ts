#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { DemoPipelineStack, DeviceKind } from 'aws4embeddedlinux-cdk-lib';
import { BuildImageDataStack } from 'aws4embeddedlinux-cdk-lib';
import { BuildImagePipelineStack, ImageKind } from 'aws4embeddedlinux-cdk-lib';
import { BuildImageRepoStack } from 'aws4embeddedlinux-cdk-lib';
import { PipelineNetworkStack } from 'aws4embeddedlinux-cdk-lib';

const app = new cdk.App();

/**
 * User Data
 */
const env = {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
};

const githubRepository = {
    org: process.env.GH_ORG ?? 'aws4embeddedlinux',
    repo: process.env.GH_REPO ?? 'meta-aws-demos',
    branch: process.env.GH_BRANCH ?? 'master',
};

/**
 * Use these default props to enable termination protection and tag related AWS
 * Resources for tracking purposes.
 */
const defaultProps: cdk.StackProps = {
    tags: { PURPOSE: 'META-AWS-BUILD' },
    terminationProtection: false,
    env,
};

/**
 * Set up the Stacks that create our Build Host.
 */
const buildImageData = new BuildImageDataStack(app, 'BuildImageData', {
    ...defaultProps,
    bucketName: `build-image-data-${env.account}-${env.region}`,
});

const buildImageRepo = new BuildImageRepoStack(app, 'BuildImageRepo', { ...defaultProps });

new BuildImagePipelineStack(app, 'BuildImagePipeline', {
    ...defaultProps,
    dataBucket: buildImageData.bucket,
    repository: buildImageRepo.repository,
    imageKind: ImageKind.Ubuntu22_04,
});

/**
 * Set up networking to allow us to securely attach EFS to our CodeBuild instances.
 */
const vpc = new PipelineNetworkStack(app, 'DemoPipelineNetwork', {
    ...defaultProps,
});

/**
 * Create a Qemu Pipeline based on meta-aws-demos.
 */
new DemoPipelineStack(app, 'QemuDemoPipeline', {
    ...defaultProps,
    githubOrg: githubRepository.org,
    githubRepo: githubRepository.repo,
    githubBranch: githubRepository.branch,
    imageRepo: buildImageRepo.repository,
    imageTag: ImageKind.Ubuntu22_04,
    device: DeviceKind.Qemu,
    vpc: vpc.vpc,
});
