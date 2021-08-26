# Original purpose: Workshop: Integrate the AWS Cloud with Responsive
# Xilinx Machine Learning at the Edge
#
# Copyright (C) 2018 Amazon.com, Inc. and Xilinx Inc.  All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

#! /bin/bash
set +x
prefix=$1
if test -z "${prefix}"; then
  echo ERROR: first argument must be the bucket prefix.
  exit 1
fi

bucket_name=${prefix}-el-cloudformation-staging
bucket_policy_location=./bucket-policy.json
echo Checking if the bucket prefix is OK.

bucket_check=$(aws s3api head-bucket --bucket ${bucket_name} 2>&1 | xargs echo | sed -e 's/.*(\(...\)).*/\1/')

echo Check completed.

if test "x${bucket_check}" == "x404"; then
    echo The bucket prefix you have chosen is OK.
    echo Creating S3 bucket [${bucket_name}]
    bucket=$(aws s3api create-bucket --output text \
                 --create-bucket-configuration '{ "LocationConstraint": "us-west-2" }' \
                 --bucket "${bucket_name}" \
                 --query Location)
    if test $? != 0; then
        echo Error creating bucket.  It could have been an itermittent problem.
        echo Please try again.
    fi

    my_ip=$(curl https://ipinfo.io/ip --stderr /dev/null)

    cat <<EOF > ${bucket_policy_location}
{
  "Version": "2012-10-17",
  "Id": "S3PolicyId1",
  "Statement": [
    {
      "Sid": "IPAllow",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::${bucket_name}/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": "${my_ip}/32"
        }
      }
    }
  ]
}
EOF

    echo Constraining bucket access to this specific device

    aws s3api put-bucket-policy --bucket ${bucket_name} --policy file://${bucket_policy_location}
    
elif test "x${bucket_check}" == "x403"; then
  echo The bucket prefix you have chosen is taken by another AWS Account.
  echo Choose another.
  exit 1
else
  echo The bucket prefix you have chosen already exists in your account and we will reuse the bucket [${bucket_name}]
fi

echo Staging CloudFormation files.
aws s3 cp --quiet --recursive --acl public-read  $(dirname $0)/../cfn/  s3://${bucket_name}/
