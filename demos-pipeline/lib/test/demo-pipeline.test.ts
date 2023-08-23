import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { DemoPipelineStack } from "../lib/demo-pipeline";
import { Repository } from "aws-cdk-lib/aws-ecr";
import { Vpc } from "aws-cdk-lib/aws-ec2";

describe("Demo Pipeline", () => {
  const env = { account: "12341234", region: "eu-central-1" };

  test("Snapshot", () => {
    const app = new cdk.App();
    const newStack = new cdk.Stack(app, "RepoStack", { env });
    const imageRepo = new Repository(newStack, "Repository", {});
    const vpc = new Vpc(newStack, "Bucket", {});

    const stack = new DemoPipelineStack(app, "MyTestStack", {
      env,
      imageRepo,
      vpc,
    });
    const template = Template.fromStack(stack);
    expect(template).toMatchSnapshot();
  });
});
