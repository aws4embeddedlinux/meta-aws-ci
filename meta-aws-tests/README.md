# info
this tests are performed before doing the ff-merge for [meta-aws](https://github.com/aws4embeddedlinux/meta-aws) `release-next` to `release` branches

in this stage there should be:
* build all recipes for all supported architectures (4 x 3 = 12 builds!)
* generating of ptest report for whole layer  (4 x 3 = 12 reports!)

# usage
run

```bash
meta-aws-tests.sh
```

for a full test, build and have time, cpu and memory!

or run a specific build and save time e.g.

```bash
meta-aws-tests.sh --releases=master --arch=qemuarm64 --package=aws-iot-fleetwise-edge

./meta-aws-tests.sh --releases=master --arch=qemuarm64 --package=aws-iot-fleetwise-edge --oldsrcuri="git://github.com/aws/aws-iot-fleetwise-edge.git;protocol=https;branch=main" --newsrcuri="git://github.com/thomas-roos/aws-iot-fleetwise-edge.git;protocol=https;branch=main"

```
