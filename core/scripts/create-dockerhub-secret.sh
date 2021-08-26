#+ /bin/bash

printf "What is your dockerhub userid (it will be used as part of the name)? "
read userid
printf "\n"

printf "What is your dockerhub password? "
read password
printf "\n"

printf "Copy this ARN for when you invoke the AWS CloudFormation script for building an image:\n"
aws secretsmanager create-secret \
    --name dockerhub_${userid} \
    --description "DockerHub login" \
    --secret-string "${password}" \
    --output text --query ARN

unset prefix
unset userid
unset password
