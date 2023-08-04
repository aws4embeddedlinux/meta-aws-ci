import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as codepipeline from "aws-cdk-lib/aws-codepipeline";
import * as codepipeline_actions from "aws-cdk-lib/aws-codepipeline-actions";
import {
  BuildSpec,
  ComputeType,
  FileSystemLocation,
  LinuxBuildImage,
  PipelineProject,
} from "aws-cdk-lib/aws-codebuild";
import { IRepository } from "aws-cdk-lib/aws-ecr";
import * as efs from "aws-cdk-lib/aws-efs";
import {
  ISecurityGroup,
  IVpc,
  Peer,
  Port,
  SecurityGroup,
} from "aws-cdk-lib/aws-ec2";
import { Bucket } from "aws-cdk-lib/aws-s3";

/**
 * The device to build demos for.
 */
export enum AdvancedDeviceKind {
  /**  Qemu x86-64 */
  Qemu = "qemu",
}

/**
 * Properties to allow customizing the build.
 */
export interface AdvancedPipelineProps extends cdk.StackProps {
  /** GitHub Repository Owner */
  readonly githubOrg?: string;
  /** GitHub Repository Name. */
  readonly githubRepo?: string;
  /** GitHub Branch Name. */
  readonly githubBranch?: string;
  /** ECR Repository where the Build Host Image resides. */
  readonly imageRepo: IRepository;
  /** Tag for the Build Host Image */
  readonly imageTag?: string;
  /** VPC where the networking setup resides. */
  readonly vpc: IVpc;
  /** Demo Device to build for. */
  readonly device?: AdvancedDeviceKind;
}

/**
 * The stack demonstrating how to build a pipeline for meta-aws-demos
 */
export class AdvancedPipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: AdvancedPipelineProps) {
    super(scope, id, props);
    /** Set up a default value for the demo BUILD_DEVICE. */
    const device = props.device ?? AdvancedDeviceKind.Qemu;

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

    const connectionArn = this.node.getContext("connectionarn");

    if (connectionArn === undefined) {
      throw new Error("No CodeStar Connection ARN provided in CDK Context!");
    }

    /** Create our CodePipeline Actions. */

    const sourceOutput = new codepipeline.Artifact();
    const sourceAction =
      new codepipeline_actions.CodeStarConnectionsSourceAction({
        output: sourceOutput,
        actionName: "Demo-Source",
        repo: props.githubRepo ?? "meta-aws-demos",
        branch: props.githubBranch ?? "master-next",
        owner: props.githubOrg ?? "aws4embeddedlinux",
        connectionArn,
        codeBuildCloneOutput: true,
      });

    const project = new PipelineProject(this, "DemoBuildProject", {
      buildSpec: BuildSpec.fromAsset(
        `assets/demo/${device}/build.buildspec.yml`
      ),
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
    new codepipeline.Pipeline(this, "DemoPipeline", {
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
    });
    fs.connections.allowFrom(securityGroup, Port.tcp(2049));

    const fsId = fs.fileSystemId;
    const region = cdk.Stack.of(this).region;

    return `${fsId}.efs.${region}.amazonaws.com:/`;
  }
}
