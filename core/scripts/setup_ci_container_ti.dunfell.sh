#! /bin/bash
prefix=$1
dockerhub_secret_arn=$2
GITHUB_ORG="${GITHUB_ORG:-aws}"
GITHUB_ORG=${GITHUB_ORG} $(dirname $0)/setup_ci_container.sh $1 $2 ti.dunfell
