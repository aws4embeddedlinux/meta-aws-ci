/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 */
import { Stack, StackProps, Construct, SecretValue } from '@aws-cdk/core';
import { CdkPipeline, SimpleSynthAction } from '@aws-cdk/pipelines';
import * as codepipeline from '@aws-cdk/aws-codepipeline';
import * as codepipeline_actions from '@aws-cdk/aws-codepipeline-actions';
import { ImageBuilderApplication } from './image-builder-application';
import { PrerequisitesStack } from './prerequisites-stack';

// This Stack contains the CodePipeline that will track changes to this package, and use it to 
// update itself and the other Stacks whenever a change is committed to the pipeline.
//
// You can deploy into multiple accounts, have multiple environments, add some validations during deployments here.
export class PipelineStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    const sourceArtifact = new codepipeline.Artifact();
    const cloudAssemblyArtifact = new codepipeline.Artifact();

    const oauthToken = SecretValue.secretsManager(PrerequisitesStack.GithubSecretName);

    const pipeline = new CdkPipeline(this, 'Pipeline', {
      pipelineName: 'DeviceImageBuilderPipeline',
      cloudAssemblyArtifact,


      sourceAction: new codepipeline_actions.GitHubSourceAction({
        actionName: 'CDK_GitHub',
        output: sourceArtifact,
        
        owner: PrerequisitesStack.GithubCdkRepositoryOwner,
        repo: PrerequisitesStack.GithubCdkRepositoryName,
        branch: PrerequisitesStack.GithubCdkRepositoryBranch,

        oauthToken,
      }),

      synthAction: SimpleSynthAction.standardNpmSynth({
        sourceArtifact,
        cloudAssemblyArtifact,
        subdirectory: PrerequisitesStack.GithubCdkSubdirectory,
        // Our dev environment use a newer version of npm creating v2 package lockfiles. update npm on build system.
        installCommand: 'npm install -g npm && npm ci',
        buildCommand: 'npm run build',
      }),
    });

    // Create our builder stage. For this demo, we only create a single stage, but the CDK Pipelines is
    // capable of constructing several. 
    // For this demo, we use the default environment variables, which will be inferred from the --profile parameter passed in
    // when building the pipeline.
    const devStage = pipeline.addApplicationStage(new ImageBuilderApplication(this, 'Testing', {
      env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION,
      },
      stage: 'testing',
    }));
  }
}
