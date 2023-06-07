import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import { BuildSpec, ComputeType, FileSystemLocation, LinuxBuildImage, PipelineProject } from 'aws-cdk-lib/aws-codebuild';
import { IRepository } from 'aws-cdk-lib/aws-ecr';
import { Bucket } from 'aws-cdk-lib/aws-s3';
import { IFileSystem, IAccessPoint } from 'aws-cdk-lib/aws-efs';
import { IVpc } from 'aws-cdk-lib/aws-ec2';
import { assert } from 'console';

export interface FileSystemAttachment {
    readonly vpc: IVpc;
    readonly filesystem: IFileSystem;
    readonly accesspoint?: IAccessPoint;
}

/**
 *
 */
export interface DemosPipelineProps extends cdk.StackProps {
    readonly githubOrg?: string;
    readonly githubRepo?: string;
    readonly codestarConnectionArn: string;
    readonly imageRepo: IRepository;
    readonly imageTag?: string;
    readonly fileSystem: FileSystemAttachment;
}

/**
 * The core pipeline stack.
 */
export class DemosPipelineStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props: DemosPipelineProps) {
        super(scope, id, props);

        const sourceOutput = new codepipeline.Artifact();
        const sourceAction = new codepipeline_actions.CodeStarConnectionsSourceAction({
            output: sourceOutput,
            actionName: 'Demo-Source',
            repo: props.githubRepo ?? 'meta-aws-demos',
            owner: props.githubOrg ?? 'aws4embeddedlinux',
            connectionArn: props.codestarConnectionArn,
            codeBuildCloneOutput: true,
        });

        const project = new PipelineProject(this, 'DemoBuildProject', {
            buildSpec: BuildSpec.fromAsset('assets/demo/qemu/build.buildspec.yml'),
            environment: {
                computeType: ComputeType.X2_LARGE,
                buildImage: LinuxBuildImage.fromEcrRepository(props.imageRepo, props.imageTag),
                privileged: true,
            },
            timeout: cdk.Duration.hours(4),
            vpc: props.fileSystem.vpc,
            fileSystemLocations: [
                FileSystemLocation.efs({
                    identifier: 'sstate_cache',
                    location: `${props.fileSystem.filesystem.fileSystemId}.efs.${props.env!.region!}.amazonaws.com:/sstate-cache`,
                    mountPoint: '/sstate-cache',
                }),
            ],
        });

        // We require this dummy output to link stages.
        const buildOutput = new codepipeline.Artifact();
        const buildAction = new codepipeline_actions.CodeBuildAction({
            input: sourceOutput,
            actionName: 'Demo-Build',
            outputs: [buildOutput],
            project,
        });

        const testProject = new PipelineProject(this, 'DemoTestProject', {
            buildSpec: BuildSpec.fromAsset('assets/demo/qemu/test.buildspec.yml'),
            environment: {
                computeType: ComputeType.X2_LARGE,
                buildImage: LinuxBuildImage.fromEcrRepository(props.imageRepo, props.imageTag),
                privileged: true,
            },
            timeout: cdk.Duration.hours(4),
            vpc: props.fileSystem.vpc,
            fileSystemLocations: [
                FileSystemLocation.efs({
                    identifier: 'sstate_cache',
                    location: `${props.fileSystem.filesystem.fileSystemId}.efs.${props.env!.region!}.amazonaws.com:/sstate-cache`,
                    mountPoint: '/sstate-cache',
                }),
            ],
        });

        const testAction = new codepipeline_actions.CodeBuildAction({
            actionName: 'Demo-Test',
            project: testProject,
            input: buildOutput,
            type: codepipeline_actions.CodeBuildActionType.TEST,
        });

        new codepipeline.Pipeline(this, 'DemoPipeline', {
            restartExecutionOnUpdate: true,
            stages: [
                {
                    stageName: 'Source',
                    actions: [sourceAction],
                },
                {
                    stageName: 'Build',
                    actions: [buildAction],
                },
                {
                    stageName: 'Test',
                    actions: [testAction],
                },
            ],
        });
    }
}
