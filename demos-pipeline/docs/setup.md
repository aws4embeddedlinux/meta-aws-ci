# Setting Up

1. Run the following:

```
npm install .
npm run build

cdk bootstrap

cdk deploy --all
```

Run the newly created pipeline `ubuntu_22_04BuildImagePipeline` from the CodePipeline console page to create the build host.

After that completes, the DemoPipeline in the CodePipeline console page is ready to run.
