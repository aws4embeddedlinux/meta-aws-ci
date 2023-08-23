import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { PipelineNetworkStack } from "../lib/network";

describe("Pipeline Networking", () => {
  const props = {
    env: { account: "111111111111", region: "eu-central-1" },
  };

  test("Snapshot", () => {
    const app = new cdk.App();
    const stack = new PipelineNetworkStack(app, props);
    const template = Template.fromStack(stack);
    expect(template).toMatchSnapshot();
  });
});
