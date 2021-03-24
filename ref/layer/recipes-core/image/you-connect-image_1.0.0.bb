SUMMARY = "You Connect Distribution Image"
DESCRIPTION = "The distribution image definition for the You Connect demonstration product."
LICENSE = "MIT"
inherit core-image

MACHINE ?= "genericx86-64"
IMAGE_INSTALL_append=" wget \
                       cloud-init \                                                                                                                                                                                            
                       packagegroup-core-full-cmdline \                                                                                                                                                                        
                       grub \
                       connman \
                       kernel-module-xen-acpi-processor \
                       you-connect"
IMAGE_FEATURES += " ssh-server-openssh"
export IMAGE_BASENAME = "you-connect"
IMAGE_NAME = "${MACHINE_NAME}_${IMAGE_BASENAME}"
# Ensure extra space for guest images
IMAGE_ROOTFS_EXTRA_SPACE = "1000000"
DISTRO_FEATURES_append = " systemd virtualization xen "
VIRTUAL-RUNTIME_init_manager = "systemd"
DISTRO_FEATURES_BACKFILL_CONSIDERED = "sysvinit"

IMAGE_LINGUAS = "en-us"
ROOTFS_PKGMANAGE_PKGS ?= '${@oe.utils.conditional("ONLINE_PACKAGE_MANAGEMENT", "none", "", "${ROOTFS_PKGMANAGE}", d)}'


