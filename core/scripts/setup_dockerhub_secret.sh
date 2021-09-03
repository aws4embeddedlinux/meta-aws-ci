#+ /bin/bash
prefix=$1
if test $# -ne 1; then
    echo you must pass in 1 argument: system prefix
    exit 1
fi

printf "What is your dockerhub username (it will be used as part of the name)? "
read username
printf "\n"

prompt="What is your dockerhub password?"
while IFS= read -p "$prompt" -r -s -n 1 char
do
    if [[ $char == $'\0' ]]
    then
        break
    fi
    prompt='*'
    password+="$char"
done
echo

printf "This is your ARN:\n"
secret_string={\"username\":\"${username}\",\"password\":\"${password}\"}
secret_arn=$(aws secretsmanager create-secret \
                 --name dockerhub_${prefix} \
                 --description "DockerHub login" \
                 --secret-string "${secret_string}" \
                 --output text --query ARN)
unset prefix
unset userid
unset password

echo ${secret_arn}
