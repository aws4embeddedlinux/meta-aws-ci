import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { BuildImageDataStack } from "../lib/build-image-data";

describe("Build Image Data", () => {
  const props = {
    bucketName: "test-bucket",
    env: { account: "111111111111", region: "eu-central-1" },
  };

  test("S3 Bucket Has Versioning Enabled", () => {
    const app = new cdk.App();
    const stack = new BuildImageDataStack(app, "MyTestStack", props);
    const template = Template.fromStack(stack);
    template.hasResourceProperties("AWS::S3::Bucket", {
      BucketName: "test-bucket",
    });

    template.allResourcesProperties("AWS::S3::Bucket", {
      VersioningConfiguration: { Status: "Enabled" },
    });
  });

  test("Snapshot", () => {
    const app = new cdk.App();
    const stack = new BuildImageDataStack(app, "MyTestStack", props);
    const template = Template.fromStack(stack);
    expect(template).toMatchSnapshot();
  });
});
