# Recipe Upgrade Helper

A tool for automating recipe upgrades for meta-aws.

See https://github.com/aws4embeddedlinux/meta-aws/blob/master/.github/workflows/auto-recipe-update.yml as a reference how to use this.

## Duplicate suppression

`upgrader update` compares each recipe as committed on the target branch against
upstream. It has no knowledge of pull requests, so while an upgrade pull request
sits unmerged the target branch still holds the old version and the same upgrade
is rediscovered on every scheduled run.

`upgrader create-pulls` therefore checks for an existing open pull request before
creating a new one. For each candidate branch it identifies the recipe and target
version, then compares against the open, bot-authored upgrade pull requests on the
same base branch:

| Existing open pull request | Action |
| --- | --- |
| none | create the pull request |
| same version | skip; delete the redundant branch |
| lower version | create, then close the older pull request as superseded |
| higher version | skip; delete the redundant branch |

### Guards

- Only pull requests authored by `meta-aws-maintainer` are considered as an
  existing upgrade, and only they are ever closed. Hand-authored pull requests
  are never matched against or closed, even when they touch the same recipe.
- Pull requests touching more than one recipe are ignored entirely. Release
  fast-forward merges and layer-wide changes are never treated as upgrades.
- A pull request carrying review or comment activity from anyone other than the
  automation is never closed.
- A branch that is still the head of an open pull request is never deleted,
  because deleting it would close that pull request.
- Versions with no digits, such as `_git.bb` recipes whose `PV` derives from
  `SRCREV`, have no comparable ordering. They compare equal, so a second
  upgrade for such a recipe is treated as a duplicate rather than a
  supersession.

### Options

- `--dry-run` reports the action for each branch without creating, closing or
  deleting anything.
- `--no-close-superseded` creates the new pull request but leaves the older one
  open.
- `--no-delete-redundant-branches` leaves branches in place when no pull request
  is created for them.

Because this runs unattended on a schedule, `--dry-run` is the recommended way
to inspect what a change to this logic would do before letting it act:

```shell
GITHUB_TOKEN=... upgrader create-pulls \
    --branch-file=branches.txt \
    --repo=aws4embeddedlinux/meta-aws \
    --target-branch=master-next \
    --dry-run
```

## Development

```shell
python3 -m venv .venv && . .venv/bin/activate
pip install -e . -r dev-requirements.txt pytest
```

Run the tests:

```shell
python -m pytest tests/
```

`tests/test_recipes.py` covers version comparison and the upgrade decision
matrix. Those functions take plain data rather than PyGithub objects
specifically so they can be tested without network access or mocks; keep new
decision logic in `upgrader/recipes.py` for the same reason.

`tests/test_proc.py::test_async_run` currently fails under Python 3.12 and
newer, which tightened `asyncio` coroutine handling. The failure predates the
duplicate-suppression work and is unrelated to it. There is no workflow running
these tests, so it has gone unnoticed.

Linting is enforced by `pre-commit` from the repository root (`black`, `isort`,
`flake8`):

```shell
pre-commit run --all-files
```

Note that `flake8` reports a spurious `E702` for semicolons appearing inside
f-string *text* when run under Python 3.12 or newer, a consequence of the PEP
701 tokenizer change. Avoid semicolons in log messages rather than adding
`noqa` comments.
