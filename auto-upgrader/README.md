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
