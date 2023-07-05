# Setting Up

TODO: CDK background...

1. Fork `meta-aws-demos` repository.
1. Create a `CodeStar` `Connection` in your AWS account with access to your fork from the previous step. This is just a dummy project, not related to previous step. Just to get a global connetion.
1. Put the ARN for this `Connection` in `bin/demos-pipeline.ts`
1. Set the account, region, and GitHub Repository Owner in `bin/demos-pipeline.ts`
1. Run the following:
```
npm install .
npm run build
npm run zip-data

cdk bootstrap

cdk deploy \
    BuildImageData \
    BuildImageRepo \
    DemoPipelineNetwork \
    BuildImagePipeline \
    QemuDemoPipeline

```

Run the resulting `BuildImagePipeline` (e.g. `ubuntu_22_04BuildImagePipeline` when using Ubuntu 22.04) to create the build host.

After that completes, the DemoPipeline is ready to run.
