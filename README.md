## meta-aws-ci: continuous integration for the meta-aws project

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
 auto-upgrader/     <= tool that is used in meta-aws to generate pull requests if an recipe upgrade is available
 docs/              <= writeups of different topics
 ff-merge/          <= script to perform -next to release branch ff merge
 release-tests/     <= script to build and ptests all Yocto meta-aws releases
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
