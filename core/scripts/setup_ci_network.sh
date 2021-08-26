#! /bin/bash
prefix=$1

echo invoking the template.

URL=https://${prefix}-el-cloudformation-staging.s3.amazonaws.com/ci_network.yml
STACKNAME=${prefix}-el-ci-network
stack_id=$(aws cloudformation create-stack --output text \
               --stack-name ${STACKNAME} \
               --template-url "${URL}" \
               --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
               --query StackId)

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