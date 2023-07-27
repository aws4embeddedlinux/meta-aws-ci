import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as ecr from "aws-cdk-lib/aws-ecr";

/**
 * The ECR Repository to store build host images.
 */
export class BuildImageRepoStack extends cdk.Stack {
  /** The respository to put the build host container in. */
  public readonly repository: ecr.IRepository;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    this.repository = new ecr.Repository(this, "BuildImageRepo", {});
  }
}
