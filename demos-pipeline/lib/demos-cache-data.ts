import * as cdk from 'aws-cdk-lib';
import * as efs from 'aws-cdk-lib/aws-efs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

/**
 * ...
 */
export interface DemosPipelineCacheProps extends cdk.StackProps {
    /** */
        readonly vpc: ec2.IVpc;
}
/**
 * ...
 */
export class DemosPipelineCache extends cdk.Stack {
    public readonly filesystem: efs.IFileSystem;
    public readonly accesspoint: efs.IAccessPoint;

    constructor(scope: Construct, id: string, props: DemosPipelineCacheProps) {
        super(scope, id, props);
        const filesystem = new efs.FileSystem(this, 'DemosPipelineFilesystem', {
            vpc: props.vpc,
        });

        this.accesspoint = filesystem.addAccessPoint('DemosPipelineAccessPoint', {
            path: '/data',
        });

        this.filesystem = filesystem;
    }
}
