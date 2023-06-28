import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

/**
 * The network resources to run the pipeline in.
 */
export class PipelineNetworkStack extends cdk.Stack {
    /** The VPC for the pipeline to reside in. */
    public readonly vpc: ec2.IVpc;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // We will create a VPC with 3 Private and Public subnets for AWS
        // Resources that have network interfaces (e.g. Connecting and EFS
        // Filesystem to a CodeBuild Project).
        this.vpc = new ec2.Vpc(this, 'PipelineVpc', {
            ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
        });
    }
}
