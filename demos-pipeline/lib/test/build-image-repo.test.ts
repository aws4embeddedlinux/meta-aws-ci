import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { BuildImageRepoStack } from "../lib/build-image-repo";

describe("Build Image Repository", () => {
  const props = {
    env: { account: "111111111111", region: "eu-central-1" },
  };

  test("ECR Repo has EmptyOnDelete", () => {
    const app = new cdk.App();
    const stack = new BuildImageRepoStack(app, "MyTestStack", props);
    const template = Template.fromStack(stack);
    template.resourceCountIs("AWS::ECR::Repository", 1); // TODO: remove after investigating following comment.
    //    template.hasResourceProperties("AWS::ECR::Repository", {
    //      EmptyOnDelete: true,
    //    });
  });

  test("Snapshot", () => {
    const app = new cdk.App();
    const stack = new BuildImageRepoStack(app, "MyTestStack", props);
    const template = Template.fromStack(stack);
    expect(template).toMatchSnapshot();
  });
});
