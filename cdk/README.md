# CDK Build Process for meta-aws-ci

This package is an [AWS CDK Pipeline](https://docs.aws.amazon.com/cdk/latest/guide/cdk_pipeline.html) demonstrating how to build AWS resources to build a Yocto Project build container, and images using
recipes for your target board. The pipeline will monitor for changes and update itself automatically.

## Expected Development Environment

* Install [NodeJS](https://nodejs.org) on your development machine. The latest LTS version is recommended.
* Upgrade NPM to version 7 or later. [View NPM upgrade instructions](https://docs.npmjs.com/try-the-latest-stable-version-of-npm)
* Run `npm install` to install dependencies.
* Run `npm run watch` in a terminal to get notified about
  TypeScript compilation issues.
* To ensure CDK builds correctly after you've made changes,
  run `cdk synth`.

## First Time Setup
* Change directory into this `cdk` folder.

* Run `npm install` to install all dependencies.

* The following steps need to be executed once to perform initial set-up and temporarily require privileged credentials.

    * The AWS account you will use to host the PipelineStack needs to be prepared using this command 
    (replace _ADMIN-PROFILE_, _ACCOUNT-ID_, and _REGION_ with values suitable to you):

    ```bash
    export CDK_NEW_BOOTSTRAP=1 
    npx cdk bootstrap --profile ADMIN-PROFILE \
        --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess \
        aws://ACCOUNT-ID/REGION
    ```
    * If you have stages deploying to other AWS accounts, you must run this command for each of them to allow the pipeline to update them.
    (replace _ADMIN-PROFILE_, _ACCOUNT-ID_, _PIPELINE-ACCOUNT-ID_ and _REGION_ with values suitable to you):
    ```bash
    export CDK_NEW_BOOTSTRAP=1 
    npx cdk bootstrap --profile ADMIN-PROFILE \
        --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess \
        --trust PIPELINE-ACCOUNT-ID \
        aws://ACCOUNT-ID/REGION
    ```

    * You must import GitHub credentials for CodeBuild to communicate with GitHub. Use this command to import a personal GitHub token:
    ```bash
    aws codebuild import-source-credentials --server-type GITHUB --auth-type PERSONAL_ACCESS_TOKEN --token <token_value>
    ```

    * You must create a secret in Secrets Manager in the account where the base 
      image will be built, with the token as a "plaintext" secret. You can use the
      same token created in the step above. Suggested name: `github_personal_token`
      
    * You must create a secret in Secrets Manager the account where the base image will be built,
      with `username` and `password` values matching your Docker Hub credentials. Suggested name: `dh`

    * Update the values `lib/prerequisites-stack.ts` file if not using the suggested secret names. 
      Other values are also configurable in that file. 


    * Manually build and deploy the pipeline once. Once successfully deployed, the pipeline will monitor changes to the repository defined 
    in pipeline-stack.ts and self-mutate automatically.
    ```bash
    git add --all
    git commit -m "initial commit"
    git push
    cdk deploy --profile=ADMIN-PROFILE
    ```

    * After the first successful deployment, priviledged credentials are no longer required.

    * After you run a deployment for the first time with the settings above, a cdk.context.json may get created automatically. This file must be committed to source control to keep track of resources
    * and settings for the self-mutate and updates to work correctly.

## Useful commands

 * `npm run build`   compile typescript to js
 * `npm run watch`   watch for changes and compile
 * `npm run test`    perform the jest unit tests
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk synth`       emits the synthesized CloudFormation template
