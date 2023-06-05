#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { DemosPipelineStack } from '../lib/demos-pipeline-stack';
import { BuildImageDataStack } from '../lib/build-image-data';
import { BuildImagePipelineStack, ImageKind } from '../lib/build-image-pipeline';
import { BuildImageRepoStack } from '../lib/build-image-repo';

const app = new cdk.App();

const env = { account: '019549032656', region: 'us-west-2' };

/**
 * Use these default props to enable termination protection and tag related AWS
 * Resources for tracking purposes.
 */
const defaultProps: cdk.StackProps = {
    tags: { PURPOSE: 'META-AWS-BUILD' },
    terminationProtection: true,
    env,
};

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

new DemosPipelineStack(app, 'DemosPipelineStack', {
    ...defaultProps,
    githubOrg: 'nateglims',
    githubRepo: 'meta-aws-demos',
    codestarConnectionArn: '',
    imageRepo: buildImageRepo.repository,
    imageTag: ImageKind.Ubuntu22_04,
});
