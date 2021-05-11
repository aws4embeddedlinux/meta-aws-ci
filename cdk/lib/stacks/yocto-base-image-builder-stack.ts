/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 */
import { Construct, SecretValue, Stack, StackProps } from '@aws-cdk/core';
import * as codebuild from '@aws-cdk/aws-codebuild';
import * as iam from '@aws-cdk/aws-iam';
import * as ecr from '@aws-cdk/aws-ecr';
import * as codepipeline from '@aws-cdk/aws-codepipeline';
import * as codepipeline_actions from '@aws-cdk/aws-codepipeline-actions';


export interface YoctoBaseImageBuilderStackProps extends StackProps {
    readonly stage: string;
    

    readonly dockerSecretName: string;
    readonly githubSecretName: string;

    readonly githubBaseImageRepositoryName: string;
    readonly githubBaseImageRepositoryOwner: string;
    readonly githubBaseImageRepositoryBranch: string;
    readonly githubBaseImageRepositorySpecLocation: string;

}

/**
 * This stack is responsible for making a docker image we will use to build Yocto with.
 * 
 * In this example, we create a CodePipeline, track incoming changes to the build process from
 * the meta-aws-ci repo on GitHub, and maintain an ECR repository where the images created by this process
 * are stored.
 */
export class YoctoBaseImageBuilderStack extends Stack {
    readonly baseImageRepository: ecr.Repository;
    readonly imageTag: string = "latest";

    constructor(scope: Construct, id: string, props: YoctoBaseImageBuilderStackProps) {
        super(scope, id, props);

        this.baseImageRepository = new ecr.Repository(this, 'YoctoBuilderImages', {
            repositoryName: 'yocto-builder-images',
        });

        // Role used by CodeBuild to run the project.
        const buildRole = new iam.Role(this, 'YoctoBuildMachineRole', {
            assumedBy: new iam.ServicePrincipal("codebuild.amazonaws.com"),
            description: `Role assumed by CodeBuild when building Build Machine images`,
        });
        this.baseImageRepository.grantPullPush(buildRole);

        // Track the changes to this repository as a trigger for this pipeline.
        const sourceArtifact = new codepipeline.Artifact();
        const sourceAction = new codepipeline_actions.GitHubSourceAction({
            actionName: 'image_builder_source',
            output: sourceArtifact,
            owner: props.githubBaseImageRepositoryOwner,
            repo: props.githubBaseImageRepositoryName,
            branch: props.githubBaseImageRepositoryBranch,
            oauthToken: SecretValue.secretsManager(props.githubSecretName),
            trigger: codepipeline_actions.GitHubTrigger.POLL,
        });

        // Create the CodeBuild Project to build the image.
        const buildProject = new codebuild.PipelineProject(this, 'YoctoBaseImageBuilder', {
            environment: {
                buildImage: codebuild.LinuxBuildImage.STANDARD_4_0,
                computeType: codebuild.ComputeType.SMALL,
                privileged: true,
                environmentVariables: {
                    "IMAGE_REPO_NAME": { value: this.baseImageRepository.repositoryName },
                    "AWS_DEFAULT_REGION": { value: this.region },
                    "AWS_ACCOUNT_ID": { value: this.account },
                    "IMAGE_TAG": { value: this.imageTag },
                    "dockerhub_username": {
                        value: `${props.dockerSecretName}:username`,
                        type: codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER
                    },
                    "dockerhub_password": {
                        value: `${props.dockerSecretName}:password`,
                        type: codebuild.BuildEnvironmentVariableType.SECRETS_MANAGER
                    }
                }
            },
            buildSpec: codebuild.BuildSpec.fromSourceFilename(props.githubBaseImageRepositorySpecLocation),
            role: buildRole
        });

        // Add the CodeBuild to the pipeline.
        const buildAction = new codepipeline_actions.CodeBuildAction({
            input: sourceArtifact,
            project: buildProject,
            actionName: 'BuildYoctoBaseImage'
        });

        // Creating a pipeline allows us to continuously build changes when they
        // are detected, instead of on a schedule.
        new codepipeline.Pipeline(this, 'YoctoBaseImageBuilder-Pipeline', {
            stages: [
                {stageName: 'Source', actions: [sourceAction]},
                {stageName: 'Build', actions: [buildAction]}
            ]
        });

    }

}