---
title: "1 – Hello Yocto! - Build your own Linux image"
weight: 10
---
Developing a project that use embedded devices requires engineering effort for selecting the right Operating System, building Board Support Package extensions and actually developing the application. In this module we tackle the first one. Choosing the right OS is a critical step in the path to production as it is, after all, the beating heart of your device: it needs to be secure, resilient, updateable, maintainable and may need to be compatible with different hardware architectures. 

The Yocto Project is an open source collaboration project that helps developers create custom Linux-based systems by providing flexible set of tools and a space where embedded developers can share technologies, software stack configurations, and best practices that can be used to create tailored Linux images based on your project needs. In this module, you’ll learn what the process is of creating an embedded OS image using the Yocto Project in the Cloud.

### What you will learn in this module

Learn how to setup a cloud development environment to make development easier and manually bake a ready-to-work image using a provided Yocto Recipe and Layers.

### What you will need

A Cloud9 Instance with 100GB available: the higher the number of vCPU available, the faster you'll be able to complete this module. (more info can be found here: https://www.yoctoproject.org/docs/latest/ref-manual/ref-manual.html#var-PARALLEL_MAKE )

The bitbake process is CPU-intensive and scales automatically with the number of vCPUs available.

![Graph that shows the time it takes to bitbake the base image based on the Cloud9 CPU instance](/images/01_hello_yocto_bitbaketimes.png)

We recommend at least a c5.9xlarge.

### Step 1 - Prepare your development environment
 
```bash
sudo apt update
sudo apt upgrade -y
```

Now install all the required packages:
```bash
sudo apt install gawk wget git-core         \
    diffstat unzip texinfo gcc-multilib   \
    chrpath socat cpio build-essential     \
    python3 python3-pip python3-pexpect  \
    xz-utils debianutils iputils-ping     \
    python3-git python3-jinja2 libegl1-mesa \
    libsdl1.2-dev xterm pylint3 -y
```

Let's set up our work folder:
```
mkdir -p $HOME/environment/src/mydev-proto
DEVHOME=$HOME/environment/src/mydev-proto
```

And clone Poky, Yocto's reference distribution that will help us build our own custom Linux Distribution.

```
git clone -b hardknott git://git.yoctoproject.org/poky $DEVHOME 
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

{{% notice note %}}
  If you receive an error like this: 
  ![](/images/01_hello_yocto_diskfull.png)
  Increase your disk space following this guide: https://docs.aws.amazon.com/cloud9/latest/user-guide/move-environment.html
  After you've resized the Cloud9's EBS from the AWS console or via CLI, if you are using Ubuntu, the main commands are:
  `sudo growpart /dev/nvme0n1 1`  and `sudo resize2fs /dev/nvme0n1p1` 
{{% /notice %}}
While we wait, we can create a new shell and proceed to the next step

### Step 3 - Integrate layers and your application layer

Let's initialize the shell and download our layers:
```
DEVHOME=$HOME/environment/src/mydev-proto
cd $DEVHOME
git clone -b hardknott git://git.openembedded.org/meta-openembedded
git clone -b hardknott https://git.yoctoproject.org/git/meta-virtualization
git clone -b hardknott https://github.com/aws4embeddedlinux/meta-aws
```

Then modify the `$DEVHOME/build/conf/bblayers.conf` file by adding the layers we downloaded previously to our new custom layer (substitute $DEVHOME with the $DEVHOME path, e.g. `home/ubuntu/environment/src/mydev-proto`)
```
$DEVHOME/meta-openembedded/meta-oe
$DEVHOME/meta-openembedded/meta-python
$DEVHOME/meta-openembedded/meta-networking
$DEVHOME/meta-aws
```

It should look like this:

```
BBLAYERS ?= " \
  /home/ubuntu/environment/src/mydev-proto/meta \
  /home/ubuntu/environment/src/mydev-proto/meta-poky \
  /home/ubuntu/environment/src/mydev-proto/meta-yocto-bsp \
  /home/ubuntu/environment/src/mydev-proto/meta-openembedded/meta-oe \
  /home/ubuntu/environment/src/mydev-proto/meta-openembedded/meta-python \
  /home/ubuntu/environment/src/mydev-proto/meta-openembedded/meta-networking \
  /home/ubuntu/environment/src/mydev-proto/meta-aws \
  "
```
This basically enables the layers in the build system.

Before baking the image, let's add the aws-ioto-device-client to the image.
Let's modify `$DEVHOME/build/conf/local.conf` and add the following line at the end of the file.
```
IMAGE_INSTALL_append = "aws-iot-device-client"
```

Wonder what this does? Check https://github.com/aws4embeddedlinux/meta-aws/blob/hardknott/recipes-iot/aws-iot-device-client/aws-iot-device-client_1.2.0.bb

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

provide user __root__ and test that the aws-device-client-sdk is installed by running the following command:
```
/sbin/aws-iot-device-client --help
```

{{% notice note %}}
  You can fix the name lookup by modifying the /etc/resolv.conf and adding your preferred nameservers (e.g. 1.1.1.1 and 1.0.0.1). 
  Wonder how to do it the "Yocto" way? Head over to: https://www.yoctoproject.org/docs/1.6/dev-manual/dev-manual.html#using-bbappend-files
{{% /notice %}}


If you want to exit the simulation, just run Ctrl+A and then press X

### Checkpoint

1. You have successfully logged onto the Cloud9 instance and set up the prerequisites
1. You have baked the image without any additional layer
1. You have modified the configuration to include the cloned layers
1. You have run the non graphical simulation of the firmware you just baked and ensured that the aws-iot-device-client sdk is present

### Considerations
Whew, this is fine if you are a single developer and are not maintaining a plethora of architectures, branches and distributions.

What if we had an automation that the bitbake process would kick-off everytime our team did a pull request/committed to the code repository and generate and archive the different layers to further speed up the bitbake times for every set of PCBs, Firmware versions, Architectures?

Follow along in the next module to discover more!
