import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import { BucketDeployment, Source } from "aws-cdk-lib/aws-s3-deployment";
import * as iam from "aws-cdk-lib/aws-iam";

/**
 * Select options for the BuildImageDataStack.
 */
export interface BuildImageDataProps extends cdk.StackProps {
  /** The bucket name for image build sources. This must be globally unique. */
  readonly bucketName: string;
}

/**
 * Input (Source) data for our Build Image Pipeline.
 */
export class BuildImageDataStack extends cdk.Stack {
  /** The bucket where source for Build Images are. */
  public readonly bucket: s3.IBucket;

  constructor(scope: Construct, id: string, props: BuildImageDataProps) {
    super(scope, id, props);

    this.bucket = this.createDeploymentBucket(props.bucketName);
  }

  /**
   * Create a bucket and S3 deployment to this bucket.
   *
   * @param bucketName The name of the bucket. Must be globally unique.
   * @param env Environment passed to the stack.
   */
  private createDeploymentBucket(bucketName: string): s3.IBucket {
    // Create a bucket, then allow a deployment Lambda to upload to it.
    const dataBucket = new s3.Bucket(this, "BuildImageDataBucket", {
      bucketName,
      versioned: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    const dataBucketDeploymentRole = new iam.Role(
      this,
      "BuildImageBucketRole",
      {
        assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
        managedPolicies: [
          iam.ManagedPolicy.fromAwsManagedPolicyName(
            "service-role/AWSLambdaBasicExecutionRole"
          ),
        ],
      }
    );

    const region = cdk.Stack.of(this).region;
    const account = cdk.Stack.of(this).account;

    dataBucketDeploymentRole.addToPolicy(
      new iam.PolicyStatement({
        actions: ["kms:Decrypt"],
        resources: [`arn:aws:kms:${region}:${account}:key/*`],
      })
    );

    new BucketDeployment(this, "BuildImageBucketDeployment", {
      // Note: Run `npm run zip-data` before deploying this stack!
      sources: [Source.asset("../lib/dist/assets/build-image")],
      destinationBucket: dataBucket,
      role: dataBucketDeploymentRole,
      extract: true,
    });

    return dataBucket;
  }
}
