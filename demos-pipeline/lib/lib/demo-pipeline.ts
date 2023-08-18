import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as codepipeline from "aws-cdk-lib/aws-codepipeline";
import * as codepipeline_actions from "aws-cdk-lib/aws-codepipeline-actions";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as efs from "aws-cdk-lib/aws-efs";

import {
  BuildSpec,
  ComputeType,
  FileSystemLocation,
  LinuxBuildImage,
  PipelineProject,
} from "aws-cdk-lib/aws-codebuild";
import { IRepository } from "aws-cdk-lib/aws-ecr";

import {
  ISecurityGroup,
  IVpc,
  Peer,
  Port,
  SecurityGroup,
} from "aws-cdk-lib/aws-ec2";
import { Bucket } from "aws-cdk-lib/aws-s3";
import { SourceRepo, DistributionKind } from "./constructs/source-repo";
import {CodeCommitTrigger} from "aws-cdk-lib/aws-codepipeline-actions";

/**
 * Properties to allow customizing the build.
 */
export interface DemoPipelineProps extends cdk.StackProps {
  /** ECR Repository where the Build Host Image resides. */
  readonly imageRepo: IRepository;
  /** Tag for the Build Host Image */
  readonly imageTag?: string;
  /** VPC where the networking setup resides. */
  readonly vpc: IVpc;
  /** The type of Layer  */
  readonly distroKind?: DistributionKind;
  /** A name for the layer-repo that is created. Default is 'layer-repo' */
  readonly layerRepoName?: string;
}

/**
 * The stack demonstrating how to build a pipeline for meta-aws-demos
 */
export class DemoPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: DemoPipelineProps) {
    super(scope, id, props);

    /** Set up networking access and EFS FileSystems. */

    const projectSg = new SecurityGroup(this, "BuildProjectSecurityGroup", {
      vpc: props.vpc,
      description: "Security Group to allow attaching EFS",
    });
    projectSg.addIngressRule(
      Peer.ipv4(props.vpc.vpcCidrBlock),
      Port.tcp(2049),
      "NFS Mount Port"
    );

    const sstateFS = this.addFileSystem("SState", props.vpc, projectSg);
    const dlFS = this.addFileSystem("Downloads", props.vpc, projectSg);
    const tmpFS = this.addFileSystem("Temp", props.vpc, projectSg);

    /** Create our CodePipeline Actions. */

    const sourceRepo = new SourceRepo(this, "SourceRepo", {
      ...props,
      repoName: props.layerRepoName ?? `layer-repo-${this.stackName}`,
      kind: props.distroKind ?? DistributionKind.Poky,
    });

    const sourceOutput = new codepipeline.Artifact();
    const sourceAction = new codepipeline_actions.CodeCommitSourceAction({
      trigger: CodeCommitTrigger.NONE,
      output: sourceOutput,
      actionName: "Source",
      repository: sourceRepo.repo,
      branch: "main",
      codeBuildCloneOutput: true,
    });

    const project = new PipelineProject(this, "DemoBuildProject", {
      buildSpec: BuildSpec.fromSourceFilename("build.buildspec.yml"),
      environment: {
        computeType: ComputeType.X2_LARGE,
        buildImage: LinuxBuildImage.fromEcrRepository(
          props.imageRepo,
          props.imageTag
        ),
        privileged: true,
      },
      timeout: cdk.Duration.hours(4),
      vpc: props.vpc,
      securityGroups: [projectSg],
      fileSystemLocations: [
        FileSystemLocation.efs({
          identifier: "tmp_dir",
          location: tmpFS,
          mountPoint: "/build-output",
        }),
        FileSystemLocation.efs({
          identifier: "sstate_cache",
          location: sstateFS,
          mountPoint: "/sstate-cache",
        }),
        FileSystemLocation.efs({
          identifier: "dl_dir",
          location: dlFS,
          mountPoint: "/downloads",
        }),
      ],
    });

    const buildOutput = new codepipeline.Artifact();
    const buildAction = new codepipeline_actions.CodeBuildAction({
      input: sourceOutput,
      actionName: "Demo-Build",
      outputs: [buildOutput],
      project,
    });

    const artifactBucket = new Bucket(this, "DemoArtifact", {
      versioned: true,
      enforceSSL: true,
    });
    const artifactAction = new codepipeline_actions.S3DeployAction({
      actionName: "Demo-Artifact",
      input: buildOutput,
      bucket: artifactBucket,
    });

    /** Now create the actual Pipeline */
    const pipeline = new codepipeline.Pipeline(this, "DemoPipeline", {
      restartExecutionOnUpdate: true,
      stages: [
        {
          stageName: "Source",
          actions: [sourceAction],
        },
        {
          stageName: "Build",
          actions: [buildAction],
        },
        {
          stageName: "Artifact",
          actions: [artifactAction],
        },
      ],
    });

    /** Here we create the logic to check for presence of ECR image on CodeCommit repo creation,
     * and only start pipeline if image exists. On CodeCommit repo updates, just trigger pipeline.  */
    const fn = new lambda.Function(this, 'OSImageCheck', {
      runtime: lambda.Runtime.PYTHON_3_10,
      handler: 'index.handler',
      code: lambda.Code.fromInline(`
import boto3

codecommit_client = boto3.client('codecommit')
ecr_client = boto3.client('ecr')
codepipeline_client = boto3.client('codepipeline')

def handler(event, context):
    response = ecr_client.describe_images(repositoryName=${props.imageRepo.repositoryName}, filter={'tagStatus': 'TAGGED'})
      for i in response['imageDetails']:
          if ${props.imageTag} in i['imageTags']:
             codepipeline_response = codepipeline_client.start_pipeline_execution(name=${pipeline.pipelineName})
             break 
             `
      ),
    });

    const startPipelinePolicy = new iam.PolicyStatement({
      actions: ['codepipeline:StartPipelineExecution'],
      resources: [pipeline.pipelineArn],
    });
    const ecrPolicy = new iam.PolicyStatement({
      actions: ['ecr:DescribeImages'],
      resources: [props.imageRepo.repositoryArn],
    });

    fn.role?.attachInlinePolicy(
        new iam.Policy(this, 'CheckOSAndStart', {
          statements: [startPipelinePolicy, ecrPolicy],
        }),
    );

    const ruleOnCreateOrUpdate = new events.Rule(this, 'BuildTriggerRule', {
      eventPattern: {
        source: ['aws.codecommit'],
        resources: [sourceRepo.repo.repositoryArn],
        detail: {
          event: ['referenceCreated', 'referenceUpdated'],
          referenceName: ['main']
        },
        detailType: ['CodeCommit Repository State Change'],
      },
    });
    ruleOnCreateOrUpdate.addTarget(new targets.LambdaFunction(fn));
  }

  /**
   * Adds an EFS FileSystem to the VPC and SecurityGroup.
   *
   * @param name - A name to differentiate the filesystem.
   * @param vpc - The VPC the Filesystem resides in.
   * @param securityGroup - A SecurityGroup to allow access to the filesystem from.
   * @returns The filesystem location URL.
   *
   */
  private addFileSystem(
    name: string,
    vpc: IVpc,
    securityGroup: ISecurityGroup
  ): string {
    const fs = new efs.FileSystem(this, `DemoPipeline${name}Filesystem`, {
      vpc,
      // TODO(nateglims): Reconsider this when development is slowing down.
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });
    fs.connections.allowFrom(securityGroup, Port.tcp(2049));

    const fsId = fs.fileSystemId;
    const region = cdk.Stack.of(this).region;

    return `${fsId}.efs.${region}.amazonaws.com:/`;
  }
}
