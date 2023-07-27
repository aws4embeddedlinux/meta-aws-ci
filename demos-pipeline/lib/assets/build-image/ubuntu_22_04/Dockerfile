FROM public.ecr.aws/lts/ubuntu:22.04_stable AS base

# This is required to avoid prompts when updating from Apt.
ARG DEBIAN_FRONTEND=noninteractive

# Install Required Packages for the Build Host
RUN apt-get update && apt-get install -y --no-install-recommends \
    gawk wget git diffstat unzip texinfo gcc build-essential chrpath \
    socat cpio python3 python3-pip python3-pexpect xz-utils debianutils \
    iputils-ping python3-git python3-jinja2 libegl1-mesa libsdl1.2-dev \
    python3-subunit mesa-common-dev zstd liblz4-tool file locales \
    uuid-runtime sysstat iproute2 openssh-client curl python-is-python3 \
    parted mtools dosfstools 

# install repo tool
RUN curl https://storage.googleapis.com/git-repo-downloads/repo > /bin/repo
RUN chmod a+rx /bin/repo

# install kas tool
RUN pip3 install PyYAML==5.3.1 && pip3 install kas==3.0.2

RUN locale-gen en_US.UTF-8

# Create a non-root user to build.
RUN groupadd -g 1000 yoctouser
RUN useradd -u 1000 -g 1000 -m yoctouser

# This seems bad, but mesa-native is looking for something in /root/.cmake for some reason.
RUN chown -R yoctouser /root

# These will be mount points for an EFS volume. This allows the cache to be reused.
RUN mkdir /downloads && chown -R yoctouser /downloads
RUN mkdir /sstate-cache && chown -R yoctouser /sstate-cache
RUN mkdir /build-output && chown -R yoctouser /build-output

ENV SSTATE_DIR=/sstate-cache
ENV DL_DIR=/downloads
ENV TMP_DIR=/tmp
ENV OUTPUT_DIR=/build-output
ENV BB_ENV_PASSTHROUGH_ADDITIONS="SSTATE_DIR DL_DIR"


USER yoctouser
