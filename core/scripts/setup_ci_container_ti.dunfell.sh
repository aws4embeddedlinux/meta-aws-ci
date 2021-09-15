#! /bin/bash
prefix=$1
dockerhub_secret_arn=$2
$(dirname $0)/setup_ci_container.sh $1 $2 ti.dunfell
