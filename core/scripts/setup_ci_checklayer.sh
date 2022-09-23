#! /bin/bash
prefix=$1
container_registry_uri=$2
yocto_release=$3
git_hub_user_org=$4

set +x

function help() {
    printf "$0 [prefix] [container_registry_uri] [yocto_release] [git_hub_user_org]\n"
    printf "\n"
    printf "prefix    the word used for the prefix naming convention.\n"
    printf "container_registry_uri 	The URI where the build machine image lives in REPOSITORY:TAG format.\n"
    printf "yocto_release    		The Yocto release, i.e. zeus, dunfell, etc.\n"
    printf "git_hub_user_org   		The GitHub organization or user to set the codebuild project for.\n"
    printf "\n"
    printf "See documentation for details.\n"
}

if test $# -ne 4; then
    printf "Error: not enough arguments.\n\n"
    help
    exit 1
fi

pushd $(dirname $0)
PWD=$(pwd)

GITHUB_ORG="${git_hub_user_org:-aws4embeddedlinux}"

echo invoking the template.

STACKNAME=${prefix}-el-checklayer-$(echo ${yocto_release} | sed -e 's/\./-/')

PREFIX_PARAM=ParameterKey=Prefix,ParameterValue=${prefix}
YOCTO_RELEASE=ParameterKey=YoctoProjectRelease,ParameterValue=${yocto_release}
CONTAINER_REGISTRY_URI=ParameterKey=ContainerRegistryUri,ParameterValue=${container_registry_uri}
NETWORK_STACK_NAME=ParameterKey=NetworkStackName,ParameterValue=${prefix}-el-ci-network
CFN_FILE=$PWD/../cfn/ci_checklayer.yml
GITHUB_SOURCE_ORG=ParameterKey=GitHubOrg,ParameterValue=${GITHUB_ORG}

if test ! -f ${CFN_FILE}; then
    echo CFN file ${CFN_FILE} not found.  ensure that the container cfn exists and
    echo there is not a typo in the distro name.
    exit 1
fi

stack_id=$(aws cloudformation create-stack --output text --query StackId \
               --stack-name ${STACKNAME} \
               --template-body file://${CFN_FILE} \
               --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
               --parameters ${NETWORK_STACK_NAME} ${CONTAINER_REGISTRY_URI} ${YOCTO_RELEASE} ${GITHUB_SOURCE_ORG}
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
