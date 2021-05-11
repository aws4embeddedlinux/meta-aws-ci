/*
 * Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 * SPDX-License-Identifier: MIT
 */
import { Stack, StackProps, Construct } from '@aws-cdk/core';
import * as ec2 from '@aws-cdk/aws-ec2';

export interface PrerequisitesStackProps extends StackProps {
    readonly stage: string;

    // If using an existing Vpc, pass in the name from the main application.
    readonly existingVpcName?: string;
}

// The prerequisites stack creates or obtains all the resources that are needed for the rest of the components
// to work. You can use the auto-created resources here to get started quickly, or replace them with lookups to
// use your existing resources. Some examples are provided.
//
// Some resources are still expected to exist in your account, primarily secrets. Consult the properties below for
// more information.
export class PrerequisitesStack extends Stack {

    // Secrets Manager: Key-value pair secret containing the docker username and password
    // Format: {
    //   "username": "docker_username",
    //   "password": "docker-api-key-f91737aaa"   
    // }
    // Used by: Base image builder, when pulling upstream images from Docker Hub
    public static readonly DockerSecretName: string = "dh";

    // Secrets Manager: Plaintext secret containing the Github token with permissions to read
    // the repository mentioned below
    // Format: "ghp_ABCDEF0iiiEXAMPLE"
    // Used by: Pipeline Stack, Image Builder when interacting with Github.
    public static readonly GithubSecretName: string = "github_personal_token";

    // VPC: Customer private cloud network set-up.
    // Used by: Image builders, to communicate between EFS caches and CodeBuild.
    public readonly Vpc: ec2.IVpc;

    // Repository: Repository where this CDK code lives.
    // Used by: Pipeline stack, to monitor changes and modify the pipeline
    // Notes: this repository must exist and be usable by your token described above
    public static readonly GithubCdkRepositoryName: string = "meta-aws-ci";
    public static readonly GithubCdkRepositoryOwner: string = "aws";
    public static readonly GithubCdkRepositoryBranch: string = "master";
    // If the CDK package isn't at the top level of the repository, enter the subdirectory here.
    public static readonly GithubCdkSubdirectory: string = "cdk";

    // Repository: Repository where the Yocto recipe code lives.
    // Used by: Image builder, to build a yocto image for this board.
    // Notes: this repository must exist and be usable by your token described above
    public static readonly GithubYoctoRecipeRepositoryName: string = "meta-aws-demos";
    public static readonly GithubYoctoRecipeRepositoryOwner: string = "aws-samples";
    public static readonly GithubYoctoRecipeRepositoryBranch: string = "master";

    // Repository: Repository where the Yocto builder CodeBuild project lives.
    // Used by: Base Image builder, to build a container for YP builds.
    // Notes: this repository must exist and be usable by your token described above
    public static readonly GithubBaseImageRepositoryName: string = "meta-aws-ci";
    public static readonly GithubBaseImageRepositoryOwner: string = "aws";
    public static readonly GithubBaseImageRepositoryBranch: string = "master";
    public static readonly GithubBaseImageRepositorySpecLocation: string = "buildspec/ci_image.yml";


    constructor(scope: Construct, id: string, props: PrerequisitesStackProps) {
        super(scope, id, props);

        // Example: Create an entirely new VPC for this project. 
        // This will create a VPC with 1 public and 1 private subnet in up to 3 AZs in the current region.
        // Note: this configuration will create multiple public subnets with NAT gateways for each one.
        //       This is the recommended VPC configuration by the CDK, but will incur costs for resources.
        this.Vpc = new ec2.Vpc(this, 'Vpc', {
            maxAzs: 3
        });

        // Example: Fetch a VPC from your account. 
        // This will cause the CDK to look for your VPC at build time, and store information about it in
        // cdk.context.json, which you should commit to source control.
        //this.Vpc = ec2.Vpc.fromLookup(this, 'Vpc', {
        //    vpcName: props.existingVpcName,
        //});
    }
}