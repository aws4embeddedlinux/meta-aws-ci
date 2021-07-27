---
title: "1 – Hello Yocto! - Build your own Linux image"
weight: 10
---
Developing a project that use embedded devices requires engineering effort for selecting the right Operating System, building Board Support Package extensions and actually developing the application. In this module we tackle the first one. Choosing the right OS is a critical step in the path to production as it is, after all, the beating heart of your device: it needs to be secure, resilient, updateable, maintainable and may need to be compatible with different hardware architectures. 

The Yocto Project is an open source collaboration project that helps developers create custom Linux-based systems by providing flexible set of tools and a space where embedded developers can share technologies, software stack configurations, and best practices that can be used to create tailored Linux images based on your project needs. In this module, you’ll learn what the process is of creating an embedded OS image using the Yocto Project in the Cloud.

### What you will learn in this module

Learn how to setup a cloud development environment to make development practices easier and manually bake a ready-to-work image using a provided Yocto Recipe and Yocto Layer.

### What will you need

Cloud9 Instance setup: the higher the number of vCPU available, the faster you'll be able to complete this module.
The bitbake process is CPU-intensive and scales very well with the number of vCPU. We recommend at least a c5.12xlarge

### Step 1 - Prepare your development environment
 
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install gawk wget git-core         \
    diffstat unzip texinfo gcc-multilib   \
    chrpath socat cpio build-essential     \
    python3 python3-pip python3-pexpect  \
    xz-utils debianutils iputils-ping     \
    python3-git python3-jinja2 libegl1-mesa \
    libsdl1.2-dev xterm pylint3 -y
```

Let's set up our work directory:
```
mkdir -p $HOME/environment/src/mydev-proto
DEVHOME=$HOME/environment/src/mydev-proto
```

And clone Poky, Yocto's reference distribution that will help us build our own custom Linux Distribution.

```
git clone -b zeus git://git.yoctoproject.org/poky $DEVHOME 
cd $DEVHOME
```

Let's finish up by __sourcing__ the init script, while specifying __build__ as the build folder.

```
source ./oe-init-build-env build 
```

### Step 2 - Bake the minimum image

While we go through the rest of the module, let's start baking the minimum core image, let's run this command.
This might take some time (17m 53s on c5.9xlarge Cloud9 instance).

```
MACHINE=qemux86-64     \
  bitbake              \
  core-image-minimal
```

### Step 3 - Integrate layers and your application layer

Now, we can download our layers:
```
git clone -b zeus git://git.openembedded.org/meta-openembedded
git clone -b zeus https://git.yoctoproject.org/git/meta-java
git clone -b zeus https://git.yoctoproject.org/git/meta-virtualization
git clone -b zeus https://github.com/aws/meta-aws
```

Then modify the `$DEVHOME/build/conf/bblayers.conf` file by adding the layers we download previously to our new custom layer (substitute $DEVHOME with the $DEVHOME path, e.g. `home/ubuntu/environment/src/mydev-proto`)
```
$DEVHOME/meta-openembedded/meta-oe
$DEVHOME/meta-openembedded/meta-python
$DEVHOME/meta-openembedded/meta-networking
$DEVHOME/meta-java
$DEVHOME/meta-aws
```

It should look like this

```
BBLAYERS ?= " \
  /home/ubuntu/environment/src/mydev-proto/meta \
  /home/ubuntu/environment/src/mydev-proto/meta-poky \
  /home/ubuntu/environment/src/mydev-proto/meta-yocto-bsp \
  /home/ubuntu/environment/src/mydev-proto/meta-openembedded/meta-oe \
  /home/ubuntu/environment/src/mydev-proto/meta-openembedded/meta-python \
  /home/ubuntu/environment/src/mydev-proto/meta-openembedded/meta-networking \
  /home/ubuntu/environment/src/mydev-proto/meta-java \
  /home/ubuntu/environment/src/mydev-proto/meta-aws \
  "
```

Now let's bake the image again.

```
MACHINE=qemux86-64     \
  bitbake              \
  core-image-minimal
```

Notice how this time, it take less time because it only needs to bake the incremental layers we just added.

### Step 4 - Test the image


```
runqemu                \
  qemux86-64           \
  core-image-minimal   \
  ext4                 \
  qemuparams="-m 2048" \
  nographic
```

If you want to exit the simulation, just run Ctrl+A and X

### Step 5 - Creating a new layer

If you wanted to create a new layer, specific for our project, type the following commands
```
bitbake-layers create-layer $DEVHOME/meta-you
bitbake-layers add-layer $DEVHOME/meta-you
```

*explain what happens*
