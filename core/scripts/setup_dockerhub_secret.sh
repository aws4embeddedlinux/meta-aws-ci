#+ /bin/bash

printf "What is your dockerhub username (it will be used as part of the name)? "
read username
printf "\n"

printf "What is your dockerhub password? "
read password
printf "\n"

printf "Copy this ARN for when you invoke the AWS CloudFormation script for building an image:\n"
secret_string={\"username\":\"${username}\",\"password\":\"${password}\"}
secret_arn=$(aws secretsmanager create-secret \
                 --name dockerhub_${username} \
                 --description "DockerHub login" \
                 --secret-string "${secret_string}" \
                 --output text --query ARN)
unset prefix
unset userid
unset password

echo ${secret_arn}
