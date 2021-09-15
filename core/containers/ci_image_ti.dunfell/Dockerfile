# Copyright 2020-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#    http://aws.amazon.com/asl/
#
# or in the "license" file accompanying this file.
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied.
# See the License for the specific language governing permissions and limitations under the License.

FROM ubuntu:18.04 AS core

ENV DEBIAN_FRONTEND="noninteractive"

# Install git, SSH, and other utilities
RUN set -ex \
    && echo 'Acquire::CompressionTypes::Order:: "gz";' > /etc/apt/apt.conf.d/99use-gzip-compression \
    && apt-get update \
    && apt install -y apt-transport-https gnupg ca-certificates \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/ubuntu stable-bionic main" | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt-get install software-properties-common -y --no-install-recommends \
    && apt-add-repository -y ppa:git-core/ppa \
    && apt-get update \
    && apt-get install git=1:2.* -y --no-install-recommends \
    && git version \
    && apt-get install -y --no-install-recommends openssh-client \
    && mkdir ~/.ssh \
    && touch ~/.ssh/known_hosts \
    && ssh-keyscan -t rsa,dsa -H github.com >> ~/.ssh/known_hosts \
    && ssh-keyscan -t rsa,dsa -H bitbucket.org >> ~/.ssh/known_hosts \
    && chmod 600 ~/.ssh/known_hosts \
    && apt-get install -y --no-install-recommends \
          apt-utils asciidoc autoconf automake build-essential bzip2 \
          bzr curl cvs cvsps dirmngr docbook-xml docbook-xsl dpkg-dev \
          e2fsprogs expect fakeroot file g++ gcc gettext gettext-base \
          groff gzip imagemagick iptables jq less libapr1 libaprutil1 \
          libargon2-0-dev libbz2-dev libc6-dev libcurl4-openssl-dev \
          libdb-dev libdbd-sqlite3-perl libdbi-perl libdpkg-perl \
          libedit-dev liberror-perl libevent-dev libffi-dev libgeoip-dev \
          libglib2.0-dev libhttp-date-perl libio-pty-perl libjpeg-dev \
          libkrb5-dev liblzma-dev libmagickcore-dev libmagickwand-dev \
          libmysqlclient-dev libncurses5-dev libncursesw5-dev libonig-dev \
          libpq-dev libreadline-dev libserf-1-1 libsqlite3-dev libssl-dev \
          libsvn1 libsvn-perl libtcl8.6 libtidy-dev libtimedate-perl \
          libtool libwebp-dev libxml2-dev libxml2-utils libxslt1-dev \
          libyaml-dev libyaml-perl llvm locales make mercurial mlocate mono-devel \
          netbase openssl patch pkg-config procps python-bzrlib \
          python-configobj python-openssl rsync sgml-base sgml-data subversion \
          tar tcl tcl8.6 tk tk-dev unzip wget xfsprogs xml-core xmlto xsltproc \
        libzip4 libzip-dev vim xvfb xz-utils zip zlib1g-dev iproute2 zstd \
    && apt-get install -y --no-install-recommends \
      gawk wget git-core diffstat unzip texinfo gcc-multilib build-essential chrpath \
      socat cpio python python3 python3-pip python3-pexpect xz-utils debianutils \
      iputils-ping python3-git python3-jinja2 libegl1-mesa libsdl1.2-dev pylint3 xterm strace \
    && rm -rf /var/lib/apt/lists/*

RUN useradd codebuild-user

#=======================End of layer: core  =================

FROM core AS tools

# AWS Tools
# https://docs.aws.amazon.com/eks/latest/userguide/install-aws-iam-authenticator.html https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ECS_CLI_installation.html
RUN curl -sS -o /usr/local/bin/aws-iam-authenticator https://amazon-eks.s3.us-west-2.amazonaws.com/1.16.8/2020-04-16/bin/linux/amd64/aws-iam-authenticator \
    && curl -sS -o /usr/local/bin/kubectl https://amazon-eks.s3.us-west-2.amazonaws.com/1.16.8/2020-04-16/bin/linux/amd64/kubectl \
    && curl -sS -o /usr/local/bin/ecs-cli https://s3.amazonaws.com/amazon-ecs-cli/ecs-cli-linux-amd64-latest \
    && curl -sS -L https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz | tar xz -C /usr/local/bin \
    && chmod +x /usr/local/bin/kubectl /usr/local/bin/aws-iam-authenticator /usr/local/bin/ecs-cli /usr/local/bin/eksctl

# Configure SSM
RUN set -ex \
    && mkdir /tmp/ssm \
    && cd /tmp/ssm \
    && wget https://s3.eu-north-1.amazonaws.com/amazon-ssm-eu-north-1/latest/debian_amd64/amazon-ssm-agent.deb \
    && dpkg -i amazon-ssm-agent.deb

# Install env tools for runtimes

#python
RUN curl https://pyenv.run | bash
ENV PATH="/root/.pyenv/shims:/root/.pyenv/bin:$PATH"

#=======================End of layer: tools  =================
FROM tools AS runtimes

#**************** PYTHON *****************************************************
ENV PYTHON_38_VERSION="3.8.3" \
    PYTHON_37_VERSION="3.7.7"

ENV PYTHON_PIP_VERSION=19.3.1

COPY tools/runtime_configs/python/$PYTHON_37_VERSION /root/.pyenv/plugins/python-build/share/python-build/$PYTHON_37_VERSION
RUN   env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install $PYTHON_37_VERSION; rm -rf /tmp/*
RUN   pyenv global  $PYTHON_37_VERSION
RUN set -ex \
    && pip3 install --no-cache-dir --upgrade --force-reinstall "pip==$PYTHON_PIP_VERSION" \
    && pip3 install --no-cache-dir --upgrade "PyYAML==5.3.1" \
    && pip3 install --no-cache-dir --upgrade setuptools wheel aws-sam-cli awscli boto3 pipenv virtualenv


COPY tools/runtime_configs/python/$PYTHON_38_VERSION /root/.pyenv/plugins/python-build/share/python-build/$PYTHON_38_VERSION
RUN   env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install $PYTHON_38_VERSION; rm -rf /tmp/*
RUN   pyenv global  $PYTHON_38_VERSION
RUN set -ex \
    && pip3 install --no-cache-dir --upgrade --force-reinstall "pip==$PYTHON_PIP_VERSION" \
    && pip3 install --no-cache-dir --upgrade "PyYAML==5.3.1" \
    && pip3 install --no-cache-dir --upgrade setuptools wheel aws-sam-cli awscli boto3 pipenv virtualenv

#**************** END PYTHON *****************************************************

#=======================End of layer: runtimes  =================

#****************        DOCKER    *********************************************
ENV DOCKER_BUCKET="download.docker.com" \
    DOCKER_CHANNEL="stable" \
    DIND_COMMIT="3b5fac462d21ca164b3778647420016315289034" \
    DOCKER_COMPOSE_VERSION="1.26.0" \
    SRC_DIR="/usr/src"

ENV DOCKER_SHA256="0f4336378f61ed73ed55a356ac19e46699a995f2aff34323ba5874d131548b9e"
ENV DOCKER_VERSION="19.03.11"

# Install Docker
RUN set -ex \
    && curl -fSL "https://${DOCKER_BUCKET}/linux/static/${DOCKER_CHANNEL}/x86_64/docker-${DOCKER_VERSION}.tgz" -o docker.tgz \
    && echo "${DOCKER_SHA256} *docker.tgz" | sha256sum -c - \
    && tar --extract --file docker.tgz --strip-components 1  --directory /usr/local/bin/ \
    && rm docker.tgz \
    && docker -v \
    # set up subuid/subgid so that "--userns-remap=default" works out-of-the-box
    && addgroup dockremap \
    && useradd -g dockremap dockremap \
    && echo 'dockremap:165536:65536' >> /etc/subuid \
    && echo 'dockremap:165536:65536' >> /etc/subgid \
    && wget -nv "https://raw.githubusercontent.com/docker/docker/${DIND_COMMIT}/hack/dind" -O /usr/local/bin/dind \
    && curl -L https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-Linux-x86_64 > /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/dind /usr/local/bin/docker-compose \
    # Ensure docker-compose works
    && docker-compose version

VOLUME /var/lib/docker
#*********************** END  DOCKER  ****************************

#=======================End of layer: corretto  =================

RUN pyenv  global $PYTHON_38_VERSION

# Configure SSH
COPY ssh_config /root/.ssh/config
COPY runtimes.yml /codebuild/image/config/runtimes.yml
COPY dockerd-entrypoint.sh /usr/local/bin/
COPY legal/THIRD_PARTY_LICENSES.txt /usr/share/doc
COPY legal/bill_of_material.txt     /usr/share/doc
COPY amazon-ssm-agent.json          /etc/amazon/ssm/

RUN which dash &> /dev/null && (\
    echo "dash dash/sh boolean false" | debconf-set-selections && \
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure dash) || \
    echo "Skipping dash reconfigure (not applicable)"

RUN locale-gen en_US.UTF-8
RUN dpkg-reconfigure locales
RUN update-locale LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

# Download and install ARM toolchains. The TI and Arago build process
# uses external toolchain.
# See: http://arago-project.org/wiki/index.php/Setting_Up_Build_Environment
#
# TI/Arago Dunfell release uses 9.2-2019.12

RUN wget --no-check-certificate https://developer.arm.com/-/media/Files/downloads/gnu-a/9.2-2019.12/binrel/gcc-arm-9.2-2019.12-x86_64-arm-none-linux-gnueabihf.tar.xz
RUN wget --no-check-certificate https://developer.arm.com/-/media/Files/downloads/gnu-a/9.2-2019.12/binrel/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu.tar.xz
RUN tar -Jxvf gcc-arm-9.2-2019.12-x86_64-arm-none-linux-gnueabihf.tar.xz -C $HOME
RUN tar -Jxvf gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu.tar.xz -C $HOME
RUN rm gcc-arm-9.2-2019.12-x86_64-arm-linux-gnueabihf.tar.xz
RUN rm gcc-arm-9.2-2019.12-x86_64-aarch64-linux-gnu.tar.xz

RUN dpkg --add-architecture i386
RUN apt-get update
RUN apt-get install -y git build-essential diffstat texinfo gawk chrpath
RUN apt-get install -y ia32-libs
RUN apt-get install -y libstdc++6:i386 libncurses5:i386 libz1:i386 libc6:i386 libc6-dev-i386 g++-multilib
RUN dpkg-reconfigure dash -fnoninteractive

# When we run in a CodeBuild context, we can integrate with CodeCommit
# only when run-as is root.  Also, when run-as is aws-yocto-builder,
# HOME is still root.  So, just give permission to aws-yocto-builder to
# root's home directory, which is a big bag of crazy.
# NOTE: the whole reason why we need to do this is bitbake requires
#       we run from a non-root context, which is completely sane.
RUN mkdir /home/aws-yocto-builder && \
    groupadd -g 70 aws-yocto-builder && \
    useradd -N -m -u 70 -g 70 aws-yocto-builder && \
    chown -R aws-yocto-builder:aws-yocto-builder /home/aws-yocto-builder && \
    chown -R aws-yocto-builder:aws-yocto-builder /root

# These are EFS mount points and must be permissioned so we can invoke the
# build and place outputs from a non-root context.
RUN mkdir /downloads    && chown -R aws-yocto-builder:aws-yocto-builder /downloads
RUN mkdir /sstate-cache && chown -R aws-yocto-builder:aws-yocto-builder /sstate-cache
RUN mkdir /build-output && chown -R aws-yocto-builder:aws-yocto-builder /build-output

USER aws-yocto-builder

ENTRYPOINT ["dockerd-entrypoint.sh"]
