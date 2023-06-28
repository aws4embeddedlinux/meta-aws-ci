# Setting Up

TODO: CDK background...

1. Create a `CodeStar` `Connection` in your AWS account.
1. Put the ARN for this `Connection` in `bin/demos-pipeline.ts`
1. TODO: customizing the pipeline, creating a new one, etc.
1. Run the following:
```
npm install .
npm run build

cdk bootstrap

npm run zip-data
cdk deploy \
    BuildImageData \
    BuildImageRepo \
    DemoPipelineNetwork \
    BuildImagePipeline \
    QemuDemoPipeline

```

Run the resulting `BuildImagePipeline` (e.g. `ubuntu_22_04BuildImagePipeline` when using Ubuntu 22.04) to create the build host.

After that completes, the DemoPipeline is ready to run.
