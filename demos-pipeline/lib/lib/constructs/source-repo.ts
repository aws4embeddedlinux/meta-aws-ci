import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { Code, Repository } from "aws-cdk-lib/aws-codecommit";

import * as path from "path";

export enum RepoKind {
  /** A Poky Based Repository */
  Poky = "poky",
  MetaAwsDemo = "meta-aws-demo",
}

export interface SourceRepoProps extends cdk.StackProps {
  readonly repoName: string;
  readonly kind: RepoKind;
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
