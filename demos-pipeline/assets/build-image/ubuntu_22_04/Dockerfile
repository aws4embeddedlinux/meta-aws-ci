FROM public.ecr.aws/lts/ubuntu:22.04_stable AS base

# This is required to avoid prompts when updating from Apt.
ARG DEBIAN_FRONTEND=noninteractive

# Install Required Packages for the Build Host
RUN apt-get update && apt-get install -y --no-install-recommends \
    gawk wget git diffstat unzip texinfo gcc build-essential chrpath \
    socat cpio python3 python3-pip python3-pexpect xz-utils debianutils \
    iputils-ping python3-git python3-jinja2 libegl1-mesa libsdl1.2-dev \
    python3-subunit mesa-common-dev zstd liblz4-tool file locales

RUN locale-gen en_US.UTF-8

# Install CA Certificates so we can clone
RUN apt-get -qq install -y ca-certificates

# Create a non-root user to build.
RUN mkdir /home/yocto && \
    groupadd -g 70 yocto && \
    useradd -N -m -u 70 -g 70 yocto && \
    chown -R yocto:yocto /home/yocto

# These will be mount points for an EFS volume. This allows the cache to be reused.
RUN mkdir /downloads && chown -R yocto:yocto /downloads
RUN mkdir /sstate-cache && chown -R yocto:yocto /sstate-cache
RUN mkdir /build-output && chown -R yocto:yocto /build-output

ENV SSTATE_DIR=/sstate-cache
ENV DL_DIR=/downloads
ENV TMP_DIR=/build-output

USER yocto
