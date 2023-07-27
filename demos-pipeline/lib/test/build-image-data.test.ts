import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { BuildImageDataStack } from "../lib/build-image-data";

test("S3 Bucket Has Versioning Enabled", () => {
  const props = { bucketName: "test-bucket" };
  const app = new cdk.App();
  // WHEN
  const stack = new BuildImageDataStack(app, "MyTestStack", props);
  // THEN
  const template = Template.fromStack(stack);
  template.hasResourceProperties("AWS::S3::Bucket", {
    BucketName: "test-bucket",
  });

  template.allResourcesProperties("AWS::S3::Bucket", {
    VersioningConfiguration: { Status: "Enabled" },
  });
});
