## meta-aws-ci: continuous integration for the meta-aws project

This project has three goals:

1. continuous integration that provides Quality accurance metrics
   across all supportable silicon vendor BSPs, matrix with the AWS
   software stacks that run on Embedded Linux.
2. pull request verification checks for meta-aws pull requests
3. provide a framework for major software stack integration testing
   using Device Tester. at the time of writing, this is limited to AWS
   IoT Greengrass.

# Project Status

The project is in the beginning stages of the first goal where build
machine definitions are being setup.

# Continuous Integration

Provides an AWS cloud native and serverless continuous integration
framework that facilitates build-stage-test.

# Pull request verification checks

Provides an AWS cloud native integration hook with the meta-aws Github
repo, providing bitbake layer integrity and verification checks. This
might be extended to incremental build-stage-test in the future.

# Device Tester integration

Device Tester provides automated testing and certification through
managed integration testing. meta-aws-ci provides the mechanisms to
coordinate edge devices under test with the harness running in the AWS
cloud.

## License

This library is licensed under the MIT-0 License.

