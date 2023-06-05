import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import { BuildSpec, ComputeType, LinuxBuildImage, PipelineProject } from 'aws-cdk-lib/aws-codebuild';
import { IRepository } from 'aws-cdk-lib/aws-ecr';
import { Bucket } from 'aws-cdk-lib/aws-s3';

/**
 *
 */
export interface DemosPipelineProps extends cdk.StackProps {
    readonly githubOrg?: string;
    readonly githubRepo?: string;
    readonly codestarConnectionArn: string;
    readonly imageRepo: IRepository;
    readonly imageTag?: string;
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
            buildSpec: BuildSpec.fromAsset('assets/demo/qemu/buildspec.yml'),
            environment: {
                computeType: ComputeType.X2_LARGE,
                buildImage: LinuxBuildImage.fromEcrRepository(props.imageRepo, props.imageTag),
            },
            timeout: cdk.Duration.hours(4),
        });

        const buildOutput = new codepipeline.Artifact();
        const buildAction = new codepipeline_actions.CodeBuildAction({
            input: sourceOutput,
            outputs: [buildOutput],
            actionName: 'Demo-Build',
            project,
        });

        const artifactBucket = new Bucket(this, 'ArtifactBucket', {});

        const artifactAction = new codepipeline_actions.S3DeployAction({
            input: buildOutput,
            bucket: artifactBucket,
            actionName: 'Demo-Artifact',
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
                    stageName: 'Artifacts',
                    actions: [artifactAction],
                },
            ],
        });
    }
}
