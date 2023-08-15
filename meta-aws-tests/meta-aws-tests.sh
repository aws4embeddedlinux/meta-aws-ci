#!/bin/bash

showHelp() {
cat << EOF
This tool will run a ptest from a specified recipe

-h, -help,          --help                  Display help
--archs                                     Set architecture to build and test
--releases                                  Set release to build and test
--package                                   Set recipe / package to build and test
--oldsrcuri                                 Remove old recipe / package srcuri
--newsrcuri                                 Set new recipe / package srcurl
--srcrev                                    Set recipe / package srcrev also AUTOREV possible
EOF
}

options=$(getopt --long "help,releases::,archs:,package:,oldsrcuri:,newsrcuri:,srcrev:" -o "h" -- "$@")

eval set -- "$options"

RELEASES="master mickledore kirkstone dunfell"
ARCHS="qemuarm64 qemux86-64"

while true
do
case "$1" in
-h|--help)
    showHelp
    exit 0
    ;;
--archs)
    shift
    export ARCHS="$1"
    ;;
--releases)
    shift
    export RELEASES="$1"
    ;;
--package)
    shift
    export PACKAGE="$1"
    ;;
--oldsrcuri)
    shift
    export OLDSRCURI="$1"
    ;;
--newsrcuri)
    shift
    export NEWSRCURI="$1"
    ;;
--srcrev)
    shift
    export SRCREV="$1"
    ;;
--)
    shift
    break;;
esac
shift
done

echo "ARCHS=$ARCHS"
echo "RELEASES=$RELEASES"
echo "PACKAGE=$PACKAGE"
echo "OLDSRCURI=$OLDSRCURI"
echo "NEWSRCURI=$NEWSRCURI"
echo "SRCREV=$SRCREV"

setup_config() {
# keep indent!
cat <<EOF >>$BUILDDIR/conf/local.conf

# set to the same as core-image-ptest
QB_MEM = "-m 1024"

# use slirp networking instead of TAP interface (require root rights)
QEMU_USE_SLIRP = "1"
TEST_SERVER_IP = "127.0.0.1"

# this will specify what test should run when running testimage cmd - oeqa layer tests + ptests:
# Ping and SSH are not required, but do help in debugging. ptest will discover all ptest packages.
TEST_SUITES = " ping ssh parselogs ptest"

# this will allow - running testimage cmd: bitbake core-image-minimal -c testimage
IMAGE_CLASSES += "testimage"

# PUT = package under test / this is set in auto.conf
PUT ?= ""
IMAGE_INSTALL:append = " ptest-runner ssh \${PUT}"

# INHERIT += "cve-check"
# include cve-extra-exclusions.inc

# INHERIT += "create-spdx"
# SPDX_PRETTY = "1"

# INHERIT += "rm_work"

# BB_ENV_PASSTHROUGH_ADDITIONS="SSTATE_DIR $BB_ENV_PASSTHROUGH_ADDITIONS" SSTATE_DIR="/sstate" ./meta-aws-release-tests.sh
SSTATE_DIR ?= "\${TOPDIR}/../../sstate-cache"
DL_DIR ?= "\${TOPDIR}/../../downloads"

# known good version
SRCREV:pn-ptest-runner = "4148e75284e443fc8ffaef425c467aa5523528ff"

EOF
}

set +exuo pipefail

for RELEASE in $RELEASES ; do

    # always delete old files, rebuilding from sstate will be fast enough
    if [ -d yocto_$RELEASE ]
    then
        echo "deleting $PWD/yocto_$RELEASE"
        tmp_del_dir=delme_$RANDOM
        mkdir $tmp_del_dir
        mv yocto_$RELEASE $tmp_del_dir
        rm -rf $tmp_del_dir &
    fi

    mkdir yocto_$RELEASE

    cd yocto_$RELEASE/

    git clone git://git.yoctoproject.org/poky -b  $RELEASE --depth=1 --single-branch
    git clone https://github.com/aws4embeddedlinux/meta-aws.git -b $RELEASE-next --depth=1 --single-branch
    git clone https://github.com/openembedded/meta-openembedded.git -b $RELEASE --depth=1 --single-branch
    git clone git://git.yoctoproject.org/meta-virtualization -b $RELEASE --depth=1 --single-branch


    source poky/oe-init-build-env build

    # add necessary layers
    bitbake-layers add-layer ../meta-openembedded/meta-oe
    bitbake-layers add-layer ../meta-openembedded/meta-python
    bitbake-layers add-layer ../meta-openembedded/meta-networking
    bitbake-layers add-layer ../meta-openembedded/meta-multimedia
    bitbake-layers add-layer ../meta-openembedded/meta-filesystems
    bitbake-layers add-layer ../meta-virtualization
    bitbake-layers add-layer ../meta-aws

    # setup build/local.conf
    setup_config

    # find all recipes in meta-aws or use package
    ALL_RECIPES=${PACKAGE-`find ../meta-aws -name *.bb -type f  | sed 's!.*/!!' | sed 's!.bb!!' | sed 's!_.*!!' | sort | uniq | sed -z 's/\n/ /g'`}

    # find all recipes having a ptest in meta-aws
    ptest_recipes=${PACKAGE-`find ../meta-aws -name *.bb -type f -print | xargs grep -l 'inherit.*ptest.*'| sed 's!.*/!!' | sed 's!.bb!!' | sed 's!_.*!!' | sort | uniq | sed -z 's/\n/ /g'`}

    # make array out of string
    ptest_recipes_array=($(echo "$ptest_recipes" | tr ',' '\n'))

    # add -ptest suffix
    ptest_recipes_names_array_with_ptest=("${ptest_recipes_array[@]/%/-ptest}")

    # make string again
    PTEST_RECIPE_NAMES_WITH_PTEST_SUFFIX="${ptest_recipes_names_array_with_ptest[@]}"

    for ARCH in $ARCHS ; do
        # do ptests for all recipes having a ptest in meta-aws
        echo PUT = \"${PTEST_RECIPE_NAMES_WITH_PTEST_SUFFIX}\" > $BUILDDIR/conf/auto.conf

        # set SRC_URI for ONE specific package
        if [ -n "$OLDSRCURI" ] && [ -n "$NEWSRCURI" ] && [ -n "$PACKAGE" ]; then
            echo SRC_URI:remove:pn-$PACKAGE = \"${OLDSRCURI}\" >> $BUILDDIR/conf/auto.conf
            echo SRC_URI:append:pn-$PACKAGE = \"${NEWSRCURI}\" >> $BUILDDIR/conf/auto.conf
        fi

        # set SRCREV for ONE specific package
        if [ -n "$SRCREV" ] && [ -n "$PACKAGE" ]; then
            echo SRCREV:pn-$PACKAGE = \"${SRCREV}\" >> $BUILDDIR/conf/auto.conf
        fi

	    # force rebuild
	    # https://stackoverflow.com/questions/51838878/execute-bitbake-recipe-discarding-what-sstate-cache-is
        # MACHINE=$ARCH bitbake $ALL_RECIPES -C unpack

        # build everything in meta-aws layer and save errors
        MACHINE=$ARCH bitbake $ALL_RECIPES -k | tee -a ../../$RELEASE-$ARCH-build.log

        # build image
        MACHINE=$ARCH bitbake core-image-minimal

        MACHINE=$ARCH bitbake core-image-minimal -c testimage

        cp $BUILDDIR/tmp/log/oeqa/testresults.json ../../$RELEASE-$ARCH-testresults.json

        # show results
        resulttool report ../../$RELEASE-$ARCH-testresults.json

    done
    # cd ../build
    cd ../

    # cd ../yocto_$RELEASE/
    cd ../
done

# search for build errors
echo  "manually check (if found) build errors: "

# note ! will invert return code,
# check for exsisting file is necessary as a non existing file would not cause an error if inverted
find . -maxdepth 1 -name "*.log" | grep . &>/dev/null && ! grep -A3 " failed"  *.log
find . -maxdepth 1 -name "*.log" | grep . &>/dev/null && ! grep -A3 " ERROR:"  *.log
find . -maxdepth 1 -name "*.json" | grep . &>/dev/null && ! grep -B3 "\"FAILED\""  *.json
