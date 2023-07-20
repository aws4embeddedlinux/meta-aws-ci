# Setting Up

1. Fork `meta-aws-demos` repository.
1. Create a GitHub [`CodeStar Connection`](https://docs.aws.amazon.com/dtconsole/latest/userguide/connections-create-github.html) with access to your Fork.
1. Run the following:
```
npm install .
npm run build

cdk bootstrap

export GH_ORG=[owner of the fork created above]

cdk deploy --context connectionarn=[CODESTAR_CONNECTION_ARN] --all
```

Run the newly created pipeline `ubuntu_22_04BuildImagePipeline` from the CodePipeline console page to create the build host.

After that completes, the DemoPipeline in the CodePipeline console page is ready to run.
