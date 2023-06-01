import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import { BuildSpec, LinuxBuildImage, PipelineProject } from 'aws-cdk-lib/aws-codebuild';
import { IRepository } from 'aws-cdk-lib/aws-ecr';

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
            environment: { buildImage: LinuxBuildImage.fromEcrRepository(props.imageRepo, props.imageTag) },
        });

        const buildAction = new codepipeline_actions.CodeBuildAction({
            input: sourceOutput,
            actionName: 'Demo-Build',
            project,
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
            ],
        });
    }
}
