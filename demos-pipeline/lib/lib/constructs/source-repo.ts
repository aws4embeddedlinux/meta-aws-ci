import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { Code, Repository } from "aws-cdk-lib/aws-codecommit";

import * as path from "path";

/**
 * The kind of Yocto Distribution built.
 */
export enum DistributionKind {
  /** A Poky Based Distribution. */
  Poky = "poky",
  /** The meta-aws Demonstration Distribution. */
  MetaAwsDemo = "meta-aws-demo",
  /** the i.mx6 Distribution from NXP. */
  imx6 = "imx6",
}

export interface SourceRepoProps extends cdk.StackProps {
  /** The name of the CodeCommit Repository created. */
  readonly repoName: string;
  /** The type of distribution to see this repository with. */
  readonly kind: DistributionKind;
}

/**
 * The repository for the Source Stage of the pipeline.
 */
export class SourceRepo extends Construct {
  /** The CodeCommit Repo itself. */
  readonly repo: Repository;

  constructor(scope: Construct, id: string, props: SourceRepoProps) {
    super(scope, id);

    this.repo = new Repository(this, "SourceRepository", {
      repositoryName: props.repoName,
      code: Code.fromDirectory(
        path.join(__dirname, "..", "..", "source-repo", props.kind),
        "main"
      ),
    });
  }
}
