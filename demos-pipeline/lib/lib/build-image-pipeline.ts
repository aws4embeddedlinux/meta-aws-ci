import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as codepipeline from "aws-cdk-lib/aws-codepipeline";
import * as codepipeline_actions from "aws-cdk-lib/aws-codepipeline-actions";
import * as codebuild from "aws-cdk-lib/aws-codebuild";
import { IRepository } from "aws-cdk-lib/aws-ecr";
import { IBucket } from "aws-cdk-lib/aws-s3";
import * as events from "aws-cdk-lib/aws-events";
import { CodePipeline } from "aws-cdk-lib/aws-events-targets";

/**
 * The type of Image to build on.
 */
export enum ImageKind {
  /** Ubuntu 22.04 (LTS) */
  Ubuntu22_04 = "ubuntu_22_04",
  /** Fedora 37 */
  Fedora37 = "fedora_37",
  /** Debian GNU/Linux 11.x (Bullseye) */
  Debian11 = "debian_11",
}

/**
 * Select options for the BuildImagePipelineStack.
 */
export interface BuildImagePipelineProps extends cdk.StackProps {
  /** The Image type to create. */
  readonly imageKind: ImageKind;
  /** The data bucket from the BuildImageDataStack */
  readonly dataBucket: IBucket;
  /** The ECR Repository to push to. */
  readonly repository: IRepository;
}

/**
 * The pipeline for building the CodeBuild Image used in other pipelines. This
 * will produce an image for an OS based on verified Yocto hosts.
 */
export class BuildImagePipelineStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: BuildImagePipelineProps) {
    super(scope, id, props);

    // Create a source action.
    const sourceOutput = new codepipeline.Artifact("BuildImageSource");
    const sourceAction = new codepipeline_actions.S3SourceAction({
      actionName: "Build-Image-Source",
      bucket: props.dataBucket,
      bucketKey: "data.zip", // TODO(glimsdal): Parameterize.
      output: sourceOutput,
    });

    // Create a build action.
    const buildImageProject = new codebuild.PipelineProject(
      this,
      "BuildImageProject",
      {
        buildSpec: codebuild.BuildSpec.fromSourceFilename(
          `${props.imageKind}/buildspec.yml`
        ),
        environment: {
          computeType: codebuild.ComputeType.LARGE,
          buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
          privileged: true,
        },
        environmentVariables: {
          ECR_REPOSITORY_URI: {
            type: codebuild.BuildEnvironmentVariableType.PLAINTEXT,
            value: props.repository.repositoryUri,
          },
          AWS_ACCOUNT_ID: {
            type: codebuild.BuildEnvironmentVariableType.PLAINTEXT,
            value: cdk.Stack.of(this).account,
          },
          AWS_DEFAULT_REGION: {
            type: codebuild.BuildEnvironmentVariableType.PLAINTEXT,
            value: cdk.Stack.of(this).region,
          },
          IMAGE_TAG: {
            type: codebuild.BuildEnvironmentVariableType.PLAINTEXT,
            value: props.imageKind,
          },
        },
      }
    );
    props.repository.grantPullPush(buildImageProject);

    const buildAction = new codepipeline_actions.CodeBuildAction({
      actionName: "Build",
      project: buildImageProject,
      input: sourceOutput,
    });

    const pipeline = new codepipeline.Pipeline(this, "BuildImagePipeline", {
      pipelineName: `${props.imageKind}BuildImagePipeline`,
      stages: [
        {
          stageName: "Source",
          actions: [sourceAction],
        },
        {
          stageName: "Build",
          actions: [buildAction],
        },
      ],
      restartExecutionOnUpdate: true,
    });

    // Run this pipeline weekly to update the image OS.
    const pipelineTarget = new CodePipeline(pipeline);
    new events.Rule(this, "WeeklySchedule", {
      schedule: events.Schedule.cron({
        weekDay: "Monday",
        minute: "0",
        hour: "6",
      }),
      targets: [pipelineTarget],
    });
  }
}
