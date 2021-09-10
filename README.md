## meta-aws-ci: continuous integration for the meta-aws project

Subtopics:

* Core CI
* Reference implementation

## Goals

This project has three goals:

1. Provide mechanisms for meta-aws and meta-aws-demos continuous
   integration and pull request verification.
2. Provide mechanisms for OEM/ODM customers wanting to streamline
   Embedded Linux delivery.
3. Provide a reference implementation that illustrates how to
   integrate and maintain AWS device software throughout the IoT
   product lifecycle.

## How this repository is organized

```text
 core/              <= mechanisms for meta-aws CI
   cfn/             <= CI/CD pipeline - CFN - Standard (all recipe targets and QA checks)
   conf/            <= bitbake local.conf configuration snippets
   containers/      <= container definitions for distribution build environments
 ref/               <= reference implementation
   cfn/             <= Infrastructure using AWS CodeCommit
   conf/            <= bitbake local configuration
   layer/           <= Reference app layer, distribution definition
     ci/            <= AWS CodeBuild buildspec file per target, repo config
 verify/            <= mechanisms for meta-aws and meta-aws-demos pull requests
 workshop/          <= workshop source for working on Yocto on AWS
```

## Repo Linting

This repository uses [pre-commit](https://pre-commit.com/) to run yaml,
whitespace, and
[cloudformation](https://github.com/aws-cloudformation/cfn-lint) linters.

To install pre-commit locally:
```shell
pip install pre-commit
pre-commit install

```

To run the checks outside of git hooks:
```shell
pre-commit run --all-files
```

## License

This library is licensed under the MIT-0 License.
