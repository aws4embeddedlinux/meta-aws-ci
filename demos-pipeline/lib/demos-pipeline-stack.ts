import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';

/**
 * The core pipeline stack.
 */
export class DemosPipelineStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);
    }
}
