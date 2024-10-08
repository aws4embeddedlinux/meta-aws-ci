# Backporting changes from master to releases
Clone and setup your fork:

git clone https://github.com/[username]/meta-aws.git
cd meta-aws
git remote add upstream https://github.com/aws4embeddedlinux/meta-aws.git
git config remote.upstream.pushurl "you really didn't want to do that"
git fetch upstream
git checkout upstream/dunfell-next -b dunfell_master_backport_$(date "+%Y-%m-%d")
Find a commit to cherry pick in master:

git cherry-pick -x <commit id>
Or a range:

git cherry-pick -x 3290ff3^..c22e729
Fix errors and git add / rm
(vscode git code view helps)

Build recipes and beware of patch changes.

You can use this to find all recipes in a layer to build them:

```

find ../meta-aws -name *.bb -type f  | sed 's!.*/!!' | sed 's!.bb!!' | sed 's!_.*!!' | sort | uniq | sed -z 's/\n/ /g'
e.g.:

bitbake `find ../meta-aws -name *.bb -type f  | sed 's!.*/!!' | sed 's!.bb!!' | sed 's!_.*!!' | sort | uniq | sed -z 's/\n/ /g'` -k
for all supported architectures (qemux64, qemuarm, qemuarm64)

e.g.:

MACHINE=qemuarm64 bitbake `find ../meta-aws -name *.bb -type f  | sed 's!.*/!!' | sed 's!.bb!!' | sed 's!_.*!!' | sort | uniq | sed -z 's/\n/ /g'` -k
or to build all recipes for all MACHINES:

 for arch in qemuarm qemuarm64 qemux86 qemux86-64 ; do MACHINE=$arch bitbake `find ../meta-aws -name *.bb -type f  | sed 's!.*/!!' | sed 's!.bb!!' | sed 's!_.*!!' | sort | uniq | sed -z 's/\n/ /g'` -k ; done
then continue cherry picking:

git cherry-pick --continue
push to your fork and create a pull request

git push
```

# Testing
All recipes from meta-aws should build for supported architectures (arm arm64 x86-64) and all ptests should pass for all releases.
We use a script to do this.

# Releasing
There is also a GitHub action available!
Releasing from A-next into A requires using Fast Forward Merges. The process is as follows:

Clone the repository locally.
Checkout the target branch.
Merge the source branch using git merge --ff-only.
If this fails, some investigation is required.
This script to do this process can be found in ff-merge folder.

Why not rebase/PR?
Using PRs to merge a staging branch into a release branch is limited to a number of methods that each have their own issues.

Merge - This will accumulate merge commits in the release branch that are not in the staging branch. If a contribution is based on the release branch, but passes through staging branch, inevitably we will encounter merge conflicts which can be completely avoided by other methods.
Rebase - Rebasing rewrites the Committer Date which causes the SHA of each commit to change. This desyncs the staging branch to show being N commits behind and N commits ahead of master. These N commits will show up in future pull requests, including contributions if they are based on the release branch. To fix this requires deleting and recreating the staging branch on each release.
Squash - Squash merge destroys commit information. This can elide who actually did commits and creates even more desync issues with the staging branch than rebasing.
