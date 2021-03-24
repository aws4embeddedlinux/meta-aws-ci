SUMMARY = "You Connect"
DESCRIPTION = "Connecting you to AWS IoT with the AWS IoT Device SDK for C++"
HOMEPAGE = "https://somewhere.com/out/there/you/connect"
LICENSE = "Apache-2.0"
PROVIDES += "you-connect"
LIC_FILES_CHKSUM = "file://LICENSE;md5=3b83ef96387f14655fc854ddc3c6bd57"

BRANCH ?= "master"
SRC_URI = "https://git-codecommit.us-east-1.amazonaws.com/v1/repos/you-connect;branch=${BRANCH}"
SRCREV = "16b73b81da29149581a433cf7b6e69fcdd11176a"

S= "${WORKDIR}/git"
PACKAGES = "${PN}"
DEPENDS = "openssl aws-iot-device-sdk-cpp-v2 googletest"
RDEPENDS_${PN} = "openssl aws-iot-device-sdk-cpp-v2"

inherit cmake

OECMAKE_BUILDPATH += "${WORKDIR}/build"
OECMAKE_SOURCEPATH += "${S}"
EXTRA_OECMAKE += "-DBUILD_SDK=OFF"
EXTRA_OECMAKE += "-DBUILD_TEST_DEPS=OFF"
EXTRA_OECMAKE += "-DBUILD_TESTING=OFF"
EXTRA_OECMAKE += "-DCMAKE_BUILD_TYPE=Release"
EXTRA_OECMAKE += "-DCMAKE_CXX_FLAGS_RELEASE=-s"

INSANE_SKIP_${PN}_append = "already-stripped"

inherit systemd
SYSTEMD_AUTO_ENABLE = "enable"
SYSTEMD_SERVICE_${PN} = "aws-iot-device-client.service"


