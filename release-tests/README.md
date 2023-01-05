# info
this tests are performed before doing the ff-merge for [meta-aws](https://github.com/aws4embeddedlinux/meta-aws) `release-next` to `release` branches

in this stage there should be:
* build all recipes for all supported architectures (4 x 3 = 12 builds!)
* generating of ptest report for whole layer  (4 x 3 = 12 reports!)
* generating of CVE report? (x reports?)
* generating of SBOM info?

# usage
run

`meta-aws-release-tests.sh`

and have time, cpu and memory!
