import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as codepipeline from "aws-cdk-lib/aws-codepipeline";
import * as codepipeline_actions from "aws-cdk-lib/aws-codepipeline-actions";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as iam from "aws-cdk-lib/aws-iam";
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
import { CodeCommitTrigger } from "aws-cdk-lib/aws-codepipeline-actions";

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
      // trigger: CodeCommitTrigger.NONE,
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

    /** Here we create the logic to check for presence of ECR image on the CodePipeline automatic triggering upon resource creation,
     * and stop the execution if the image does not exist.  */
    const fnOnPipelineCreate = new lambda.Function(
      this,
      "OSImageCheckOnStart",
      {
        runtime: lambda.Runtime.PYTHON_3_10,
        handler: "index.handler",
        code: lambda.Code.fromInline(`
import boto3
import json

ecr_client = boto3.client('ecr')
codepipeline_client = boto3.client('codepipeline')

def handler(event, context):
  print("Received event: " + json.dumps(event, indent=2))
  response = ecr_client.describe_images(repositoryName='${props.imageRepo.repositoryName}', filter={'tagStatus': 'TAGGED'})
  for i in response['imageDetails']:
    if '${props.imageTag}' in i['imageTags']:
      break
  else:
    print('OS image not found. Stopping execution.')
    response = codepipeline_client.stop_pipeline_execution(
    pipelineName=event['detail']['pipeline'],
    pipelineExecutionId=event['detail']['execution-id'],
    abandon=False,
    reason='OS image not found in ECR repository. Stopping pipeline until image is present.')
    `),
      }
    );
    const stopPipelinePolicy = new iam.PolicyStatement({
      actions: ["codepipeline:StopPipelineExecution"],
      resources: ["*"], //TODO: fix.
    });

    const ecrPolicy = new iam.PolicyStatement({
      actions: ["ecr:DescribeImages"],
      resources: [props.imageRepo.repositoryArn],
    });
    fnOnPipelineCreate.role?.attachInlinePolicy(
      new iam.Policy(this, "CheckOSAndStop", {
        statements: [stopPipelinePolicy, ecrPolicy],
      })
    );

    const pipelineCreateRule = new events.Rule(this, "OnPipelineStartRule", {
      eventPattern: {
        detailType: ["CodePipeline Pipeline Execution State Change"],
        source: ["aws.codepipeline"],
        detail: {
          state: ["STARTED"],
          "execution-trigger": {
            "trigger-type": ["CreatePipeline"],
          },
        },
      },
    });
    pipelineCreateRule.addTarget(
      new targets.LambdaFunction(fnOnPipelineCreate)
    );

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
