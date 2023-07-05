#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { DemoPipelineStack, DeviceKind } from '../lib/demo-pipeline';
import { BuildImageDataStack } from '../lib/build-image-data';
import { BuildImagePipelineStack, ImageKind } from '../lib/build-image-pipeline';
import { BuildImageRepoStack } from '../lib/build-image-repo';
import { PipelineNetworkStack } from '../lib/network';

const app = new cdk.App();

const env = { account: '743600277648', region: 'eu-central-1' };
const githubRepository = { org: 'thomas-roos', repo: 'meta-aws-demos', branch: 'pipeline' };
const codestarConnectionArn = 'arn:aws:codestar-connections:eu-central-1:743600277648:connection/6cd98bb7-5c5f-4227-95da-4e58a6629fbb';

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
    codestarConnectionArn: codestarConnectionArn,
    imageRepo: buildImageRepo.repository,
    imageTag: ImageKind.Ubuntu22_04,
    device: DeviceKind.Qemu,
    vpc: vpc.vpc,
});
