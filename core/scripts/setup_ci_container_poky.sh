#! /bin/bash
prefix=$1
dockerhub_secret_arn=$2
set +x
if test $# -ne 3; then
    echo you must pass in 3 arguments: prefix then dockerhub secret arn
    exit 1
fi

echo invoking the template.

URL=https://${prefix}-el-cloudformation-staging.s3.amazonaws.com/ci_container_poky.yml
STACKNAME=${prefix}-el-ci-container-poky
PREFIX_PARAM=ParameterKey=Prefix,ParameterValue=${prefix}
NETWORK_STACK_NAME=ParameterKey=NetworkStackName,ParameterValue=${prefix}-el-ci-network
DOCKERHUB_SECRET_ARN=ParameterKey=DockerhubSecretArn,ParameterValue=${dockerhub_secret_arn}

stack_id=$(aws cloudformation create-stack --output text --query StackId \
               --stack-name ${STACKNAME} \
               --template-url "${URL}" \
               --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
               --parameters ${NETWORK_STACK_NAME} ${DOCKERHUB_SECRET_ARN} ${PREFIX_PARAM}
               )

echo stack_id is [${stack_id}]
deployment_status=CREATE_IN_PROGRESS

while test "${deployment_status}" == "CREATE_IN_PROGRESS"; do
    echo deployment status: $deployment_status ... wait three seconds
    sleep 3

    deployment_status=$(aws cloudformation describe-stacks \
                            --stack-name ${STACKNAME} \
                            --query "Stacks[?StackName=='${STACKNAME}'].StackStatus" \
                            --output text)
done

echo deployment status: $deployment_status

if test "x${deployment_status}" != 'xCREATE_COMPLETE'; then
    echo Cloudformation script did not complete successfully.
    exit 1
fi
