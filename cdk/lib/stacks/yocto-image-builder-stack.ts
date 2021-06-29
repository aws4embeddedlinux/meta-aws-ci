/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 */
import { Construct, SecretValue, Stack, StackProps, RemovalPolicy } from '@aws-cdk/core';
import { Bucket } from '@aws-cdk/aws-s3';
import * as codebuild from '@aws-cdk/aws-codebuild';
import * as iam from '@aws-cdk/aws-iam';
import * as ec2 from '@aws-cdk/aws-ec2';
import * as ecr from '@aws-cdk/aws-ecr';
import * as efs from '@aws-cdk/aws-efs';
import * as codepipeline from '@aws-cdk/aws-codepipeline';
import * as codepipeline_actions from '@aws-cdk/aws-codepipeline-actions';

export interface YoctoImageBuilderStackProps extends StackProps {

    readonly stage: string;
    readonly vpc: ec2.IVpc;

    readonly githubSecretName: string;
    readonly githubYoctoRecipeRepositoryName: string;
    readonly githubYoctoRecipeRepositoryOwner: string;
    readonly githubYoctoRecipeRepositoryBranch: string;

    readonly yoctoProjectRelease?: string;
    readonly machineType?: string;
    readonly projectType?: string;
    
    readonly baseImageRepository: ecr.Repository;
    readonly imageTag: string;
}

export class YoctoImageBuilderStack extends Stack {
    constructor(scope: Construct, id: string, props: YoctoImageBuilderStackProps) {
        super(scope, id, props);

        // Provide some default values for our props above
        const { 
            yoctoProjectRelease = "dunfell", 
            machineType = "raspberrypi4-64", 
            projectType = "aws-iot-greengrass-v2" 
        } = props;


        // Bucket where the built artifacts will live.
        const buildBucket = new Bucket(this, 'YoctoImageBuildBucket', {
            bucketName: `device-images-${props.stage}--${this.account}-${this.region}`,
            removalPolicy: RemovalPolicy.RETAIN
        });

        // Role used by CodeBuild to run the project.
        const buildRole = new iam.Role(this, 'YoctoBuildRole', {
            assumedBy: new iam.ServicePrincipal("codebuild.amazonaws.com"),
            description: `Role assumed by CodeBuild when building Yocto Project for ${machineType}/${yoctoProjectRelease}`,
        });

        // Create EFS storage for caching intermediary artifacts to speed up build process.
        const sstateFilesystem = new efs.FileSystem(this, 'SStateCache', {
            vpc: props.vpc,
            encrypted: false,
            fileSystemName: `${this.stackName}/sstate-cache`,
            enableAutomaticBackups: true,
            lifecyclePolicy: efs.LifecyclePolicy.AFTER_30_DAYS,
            performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
            throughputMode: efs.ThroughputMode.BURSTING,
        });

        const downloadCacheFilesystem = new efs.FileSystem(this, 'DownloadCache', {
            vpc: props.vpc,
            encrypted: false,
            fileSystemName: `${this.stackName}/download`,
            enableAutomaticBackups: true,
            lifecyclePolicy: efs.LifecyclePolicy.AFTER_30_DAYS,
            performanceMode: efs.PerformanceMode.GENERAL_PURPOSE,
            throughputMode: efs.ThroughputMode.BURSTING
        });

        const oauthToken = SecretValue.secretsManager(props.githubSecretName);

        // This repository contains the logic to build the yocto image for our requested platform
        const sourceArtifact = new codepipeline.Artifact();
        const sourceAction = new codepipeline_actions.GitHubSourceAction({
            actionName: 'yocto_recipe_source',
            output: sourceArtifact,
            owner: props.githubYoctoRecipeRepositoryOwner,
            repo: props.githubYoctoRecipeRepositoryName,
            branch: props.githubYoctoRecipeRepositoryBranch,
            oauthToken: oauthToken,
            // Use Poll if the token does not have authorization to add=
            // hooks to the target repository.
            trigger: codepipeline_actions.GitHubTrigger.POLL,
        });

        // Since we depend on meta-aws, also add tracking for changes to this repository.
        const metaArtifact = new codepipeline.Artifact();
        const metaSourceAction = new codepipeline_actions.GitHubSourceAction({
            actionName: 'meta_aws',
            output: metaArtifact,
            owner: 'aws',
            repo: 'meta-aws',
            oauthToken: oauthToken,
            trigger: codepipeline_actions.GitHubTrigger.POLL,
        });

        const buildProject = new codebuild.PipelineProject(this, `YoctoBuild-${machineType}-${projectType}-${yoctoProjectRelease}`, {
            badge: false,
            vpc: props.vpc,
            role: buildRole,
            description: `Build process for Yocto ${machineType}/${projectType}:${yoctoProjectRelease}`,
            environment: {
                privileged: true,
                computeType: codebuild.ComputeType.X2_LARGE,
                buildImage: codebuild.LinuxBuildImage.fromEcrRepository(
                    props.baseImageRepository,
                    props.imageTag
                ),
                environmentVariables: {
                    "DISTRIBUTION_S3": { value: buildBucket.bucketName },
                    "YP_RELEASE": { value: yoctoProjectRelease },
                },
            },
            fileSystemLocations: [
                codebuild.FileSystemLocation.efs({
                    identifier: 'sstate',
                    mountPoint: '/sstate-cache',
                    location: `${sstateFilesystem.fileSystemId}.efs.${this.region}.amazonaws.com:/`
                }),
                codebuild.FileSystemLocation.efs({
                    identifier: 'downloads',
                    mountPoint: '/downloads',
                    location: `${downloadCacheFilesystem.fileSystemId}.efs.${this.region}.amazonaws.com:/`
                }),
            ],
            buildSpec: codebuild.BuildSpec.fromSourceFilename(`${machineType}/${projectType}/${yoctoProjectRelease}/buildspec.yml`),
        });
        //Grant access to these EFS resources by the CodeBuild project
        sstateFilesystem.connections.allowDefaultPortFrom(buildProject);
        downloadCacheFilesystem.connections.allowDefaultPortFrom(buildProject);

        const buildArtifact = new codepipeline.Artifact();
        const buildAction = new codepipeline_actions.CodeBuildAction({
            input: sourceArtifact,
            extraInputs: [metaArtifact],
            outputs: [buildArtifact],
            project: buildProject,
            actionName: 'BuildYoctoImage'
        });

        const deployAction = new codepipeline_actions.S3DeployAction({
            actionName: 'UploadProdImage',
            objectKey: `${yoctoProjectRelease}/${machineType}/${projectType}`,
            extract: true,
            input: buildArtifact,
            bucket: buildBucket
        });
        
        // Creating a pipeline allows us to continuously build changes when they
        // are detected, instead of on a schedule.
        new codepipeline.Pipeline(this, 'YoctoBaseImageBuilder-Pipeline', {
            stages: [
                {stageName: 'Source', actions: [sourceAction, metaSourceAction]},
                {stageName: 'Build', actions: [buildAction]},
                {stageName: 'Package', actions: [deployAction]},
            ]
        });
    }
}
