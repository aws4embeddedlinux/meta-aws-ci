#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { DemosPipelineStack } from '../lib/demos-pipeline-stack';
import { BuildImageDataStack } from '../lib/build-image-data';
import { Repository } from 'aws-cdk-lib/aws-ecr';
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

new DemosPipelineStack(app, 'DemosPipelineStack', {
    /* If you don't specify 'env', this stack will be environment-agnostic.
     * Account/Region-dependent features and context lookups will not work,
     * but a single synthesized template can be deployed anywhere. */
    /* Uncomment the next line to specialize this stack for the AWS Account
     * and Region that are implied by the current CLI configuration. */
    // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
    /* Uncomment the next line if you know exactly what Account and Region you
     * want to deploy the stack to. */
    // env: { account: '123456789012', region: 'us-east-1' },
    /* For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html */
    ...defaultProps,
});

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
