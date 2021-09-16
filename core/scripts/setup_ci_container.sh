#! /bin/bash
prefix=$1
dockerhub_secret_arn=$2
distro=$3

set +x

function help() {
    printf "$0 [prefix] [dh_arn] [distro]\n"
    printf "\n"
    printf "prefix    the word used for the prefix naming convention.\n"
    printf "dh_arn    the ARN for the dockerhub secret in AWS Secrets Manager.\n"
    printf "distro    the target distribution name.\n"
    printf "\n"
    printf "See documentation for details.\n"
}

if test $# -ne 3; then
    printf "Error: not enough arguments.\n\n"
    help
    exit 1
fi

pushd $(dirname $0)
PWD=$(pwd)

GITHUB_ORG="${GITHUB_ORG:-aws}"

echo invoking the template.

STACKNAME=${prefix}-el-ci-container-$(echo ${distro} | sed -e 's/\./-/')

PREFIX_PARAM=ParameterKey=Prefix,ParameterValue=${prefix}
NETWORK_STACK_NAME=ParameterKey=NetworkStackName,ParameterValue=${prefix}-el-ci-network
DOCKERHUB_SECRET_ARN=ParameterKey=DockerhubSecretArn,ParameterValue=${dockerhub_secret_arn}
CFN_FILE=$PWD/../cfn/ci_container_${distro}.yml
GITHUB_SOURCE_ORG=ParameterKey=GithubSourceOrg,ParameterValue=${GITHUB_ORG}

if test ! -f $CFN_FILE; then
    echo CFN file ${CFN_FILE} not found.  ensure that the container cfn exists and
    echo there is not a typo in the distro name.
    exit 1
fi

stack_id=$(aws cloudformation create-stack --output text --query StackId \
               --stack-name ${STACKNAME} \
               --template-body file://$PWD/../cfn/ci_container_${distro}.yml \
               --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
               --parameters ${NETWORK_STACK_NAME} ${DOCKERHUB_SECRET_ARN} ${PREFIX_PARAM} ${GITHUB_SOURCE_ORG}
               )

if test $? -ne 0; then
    printf "Error: template invocation failed.\n"
    exit 1
fi

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
