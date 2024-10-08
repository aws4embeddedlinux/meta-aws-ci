# PTest Setup
## Recipe Setup
The public docs can be found on the yocto wiki and note there is this about testimages (an image include ptest and oeqa tests)

## Inherit ptest
Create an executable shell script called `run-ptest`. This will need to produce a specific output of described in the wiki.
For CTest, I found it easiest to process the JUnit XML with a simple python script.
Setup Image
In your local conf add the following:

```
MACHINE = "qemux86-64"

DISTRO_FEATURES:append = " ptest"
EXTRA_IMAGE_FEATURES += "ptest-pkgs"
IMAGE_INSTALL:append = " ptest-runner [PACKAGE NAME] ssh"
IMAGE_CLASSES += "testimage"
# Required to disable KVM/hypervisor mode.
QEMU_USE_KVM = ""
# Ping and SSH are not required, but do help in debugging. ptest will discover all ptest packages.
TEST_SUITES = " ping ssh ptest"
# Increased memory is typically required.
QB_MEM = "-m 4096"
# enable slirp networking
QEMU_USE_SLIRP = "1"
TEST_SERVER_IP = "127.0.0.1"
minimal do this:

# Required to disable KVM/hypervisor mode.
QEMU_USE_KVM = ""

# use slirp networking instead of TAP interface (require root rights)
QEMU_USE_SLIRP = "1"
TEST_SERVER_IP = "127.0.0.1"


# aws-c-common-ptest = ptest package for aws-c-common
IMAGE_INSTALL:append = " ptest-runner ssh aws-c-common-ptest"


# this will allow - running testimage cmd: bitbake core-image-minimal -c testimage
IMAGE_CLASSES += "testimage"

# this will specify what test should run when running testimage cmd - oeqa layer tests + ptests:
# Ping and SSH are not required, but do help in debugging. ptest will discover all ptest packages.
TEST_SUITES = " ping ssh ptest"
```

## Executing
Option 1: Create the image, log into it and manually run `ptest-runner`.
Option 2: Run the command with `bitbake core-image-minimal -c testimage`.
