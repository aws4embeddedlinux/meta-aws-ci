#! /bin/bash
prefix=$1
container_uri=$2
vendor=$3
board=$4
demo=$5
release=$6
set +x
if test $# -ne 3; then
    echo $0 [prefix] [container_uri] [vendor] [board] [demo] [yocto_release]
    echo See online documentation for more details.
    exit 1
fi

echo invoking the template.

URL=https://${prefix}-el-cloudformation-staging.s3.amazonaws.com/build_demos_prod.yml
STACKNAME=${prefix}-el-ci-build-${vendor}-${board}-${demo}-${release}
PREFIX_PARAM=ParameterKey=Prefix,ParameterValue=${prefix}
NETWORK_STACK_NAME=ParameterKey=NetworkStackName,ParameterValue=${prefix}-el-ci-network
CONTAINER_ARN=ParameterKey=ContainerRegisterUri,ParameterValue=${container_uri}
VENDOR=ParameterKey=DemoVendor,ParameterValue=${vendor}
BOARD=ParameterKey=DemoBoard,ParameterValue=${board}
DEMO=ParameterKey=DemoName,ParameterValue=${demo}
RELEASE=ParameterKey=YoctoProjectRelease,ParameterValue=${release}

stack_id=$(aws cloudformation create-stack --output text --query StackId \
               --stack-name ${STACKNAME} \
               --template-url "${URL}" \
               --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
                              CAPABILITY_AUTO_EXPAND \
               --parameters ${NETWORK_STACK_NAME} ${CONTAINER_ARN} \
                            ${PREFIX_PARAM} ${VENDOR} ${BOARD} ${DEMO} ${RELEASE}
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
