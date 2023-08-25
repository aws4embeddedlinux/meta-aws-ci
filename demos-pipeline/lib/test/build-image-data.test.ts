import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { BuildImageDataStack } from "../lib/build-image-data";

describe("Build Image Data", () => {
  const props = {
    bucketName: "test-bucket",
    removalPolicy: cdk.RemovalPolicy.DESTROY,
    autoDeleteObjects: true,
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
    /* We must change some randomly generated file names used in the S3 asset construct. */
    const templateWithRandomKeys = Template.fromStack(stack);
    const templateWithConstKeys = JSON.parse(
      JSON.stringify(templateWithRandomKeys.toJSON()).replace(
        /[a-z0-9]{64}\.zip/g,
        "arbitrary-file.zip"
      )
    );
    expect(templateWithConstKeys).toMatchSnapshot();
  });
});
