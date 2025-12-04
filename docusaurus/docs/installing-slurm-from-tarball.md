# Installing Slurm from Tarball

This guide explains how to deploy pre-built, GPG-signed Slurm software tarballs that are published by **slurm-factory**. Tarballs provide a relocatable, module-enabled Slurm stack that extracts quickly onto any compatible Linux host or container.

## When to Choose the Tarball Workflow

Use the tarball-based install when you:
- ✅ Need an **offline-friendly** bundle with all binaries, modules, and runtime assets
- ✅ Want to avoid installing Spack or Docker on the target machine
- ✅ Prefer a reproducible image build pipeline fed by a single artifact
- ✅ Plan to distribute Slurm to multiple machines via configuration management

Stick with the [buildcache workflow](./installing-slurm-from-buildcache.md) when you need per-node dependency resolution or incremental package updates through Spack.

## Artifact Layout and URLs

Tarballs are published under the CloudFront distribution with the following URL pattern:

```
https://slurm-factory-spack-binary-cache.vantagecompute.ai/{toolchain}/{slurm_version}/
```

Each directory contains:

```
slurm-{slurm_version}-{toolchain}-software.tar.gz      # Tarball
slurm-{slurm_version}-{toolchain}-software.tar.gz.asc  # Detached GPG signature
```

The tarball extracts to a self-contained layout:

```
view/                                 # Relocated Slurm prefix
assets/modules/                       # Lmod modulefiles
```

Pick a tarball that matches your host distribution (see [Build Artifacts](./build-artifacts.md) for the compatibility matrix).

## Prerequisites

- RHEL-compatible host (Rocky, Alma, CentOS) 7/8/9 or Ubuntu 18.04+
- Root or sudo privileges to install into `/opt`
- Packages: `curl`, `tar`, `gnupg`, `lua`, `lmod`, and base build tools (`yum-utils`/`dnf-plugins-core` or `apt`)
- Internet access to `slurm-factory-spack-binary-cache.vantagecompute.ai` (unless you mirror the tarball internally)

## Download and Verify the Tarball

```bash
export CLOUDFRONT_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai
export SLURM_VERSION=25.11
export TOOLCHAIN=noble  # or: jammy, resolute, rockylinux10, rockylinux9, rockylinux8

# Fetch tarball and signature
mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball
curl -O "${CLOUDFRONT_URL}/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz"
curl -O "${CLOUDFRONT_URL}/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc"
```

### Verify the Tarball

```bash
gpg --keyserver keyserver.ubuntu.com --auto-key-retrieve \
        --verify slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
                         slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz
```

Verification succeeds when the output includes `gpg: Good signature from "slurm-factory"`.

## Extract the Tarball

```bash
sudo mkdir -p /opt/slurm-factory
sudo tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory
sudo chown -R root:root /opt/slurm-factory
```

After extraction you will have a relocatable layout:

```text
/opt/slurm-factory/
├── view/                 # Slurm binaries, libraries, etc.
├── assets/modules/       # Lmod modulefiles
├── etc/                  # Example configs and systemd units
├── share/                # Helper scripts and docs
└── manifest.yml          # Build metadata (versions, hashes)
```

## Configure Environment Modules

```bash
# Make the provided modulefiles discoverable
export SLURM_FACTORY_PREFIX=/opt/slurm-factory
export MODULEPATH="${SLURM_FACTORY_PREFIX}/assets/modules:${MODULEPATH}"
source /etc/profile.d/lmod.sh

# Load Slurm into the environment
module load slurm
module list

# Optional: persist MODULEPATH for all users
echo "export MODULEPATH=${SLURM_FACTORY_PREFIX}/assets/modules:\${MODULEPATH}" | sudo tee /etc/profile.d/slurm-factory.sh
```

## Minimal Runtime Configuration

1. Create `/etc/slurm` and seed `slurm.conf` (sample files are in `/opt/slurm-factory/etc`).
2. Pick an authentication plugin:
   - `auth/munge` (default) requires Munge key distribution
   - `auth/slurm` avoids Munge for minimal testing and is used in the Docker snippets below
3. Ensure spool and log directories exist (`/var/spool/slurm`, `/var/log/slurm`).
4. Start `slurmctld` and `slurmd`:

```bash
sudo /opt/slurm-factory/view/sbin/slurmctld
sudo /opt/slurm-factory/view/sbin/slurmd
```

## Dockerfile Examples

Each Dockerfile below downloads, verifies, and extracts the tarball, then bootstraps a simple single-node configuration using `auth/slurm`. Adjust `SLURM_VERSION`, `TOOLCHAIN`, and `TARBALL_URL` to match the artifact you need.

### Rocky Linux 10 (RHEL 10 Compatible)

```dockerfile
FROM rockylinux:10

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=rockylinux10
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN yum -y install epel-release && \
    yum -y install curl gnupg lmod lua lua-posix which && \
    yum clean all && rm -rf /var/cache/yum

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
        curl -fsSLO "${TARBALL_URL}.asc" && \
        curl -fsSLO "${TARBALL_URL}" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Rocky Linux 8

```dockerfile
FROM rockylinux:8

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=rockylinux8
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN dnf -y install epel-release && \
    dnf -y install curl gnupg2 lmod lua-posix && \
    dnf clean all && rm -rf /var/cache/dnf

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
        curl -fsSLO "${TARBALL_URL}.asc" && \
        curl -fsSLO "${TARBALL_URL}" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Rocky Linux 9

```dockerfile
FROM rockylinux:9

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=rockylinux9
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN dnf -y install epel-release && \
    dnf -y install curl gnupg2 lmod lua-posix && \
    dnf clean all && rm -rf /var/cache/dnf

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
        curl -fsSLO "${TARBALL_URL}.asc" && \
        curl -fsSLO "${TARBALL_URL}" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Ubuntu 18.04 (Bionic)

```dockerfile
FROM ubuntu:18.04

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=bionic
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg lmod lua5.3 lua-posix && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
        curl -fsSLO "${TARBALL_URL}.asc" && \
        curl -fsSLO "${TARBALL_URL}" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Ubuntu 20.04 (Focal)

```dockerfile
FROM ubuntu:20.04

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=focal
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg lmod lua5.3 lua-posix && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
        curl -fsSLO "${TARBALL_URL}.asc" && \
        curl -fsSLO "${TARBALL_URL}" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Ubuntu 22.04 (Jammy)

```dockerfile
FROM ubuntu:22.04

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=jammy
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg lmod lua5.3 lua-posix && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
        curl -fsSLO "${TARBALL_URL}.asc" && \
        curl -fsSLO "${TARBALL_URL}" && \
        gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
            slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
            slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Ubuntu 24.04 (Noble)

```dockerfile
FROM ubuntu:24.04

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=noble
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg lmod lua5.4 lua-posix && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
    curl -fsSLO "${TARBALL_URL}" && \
    curl -fsSLO "${TARBALL_URL}.asc" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

### Ubuntu 26.04 (Planned)

> Ubuntu 26.04 is not yet GA; the `ubuntu:devel` tag tracks the current development snapshot. Adjust package names if Canonical changes defaults before release.

```dockerfile
FROM ubuntu:devel

ARG SLURM_VERSION=25.11
ARG TOOLCHAIN=oracular
ARG TARBALL_URL=https://slurm-factory-spack-binary-cache.vantagecompute.ai/${TOOLCHAIN}/${SLURM_VERSION}/slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg lmod lua5.4 lua-posix && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/slurm-tarball && cd /tmp/slurm-tarball && \
    curl -fsSLO "${TARBALL_URL}" && \
    curl -fsSLO "${TARBALL_URL}.asc" && \
    gpg --batch --keyserver keyserver.ubuntu.com --auto-key-retrieve --verify \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz.asc \
        slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz && \
    mkdir -p /opt/slurm-factory && \
    tar -xzf slurm-${SLURM_VERSION}-${TOOLCHAIN}-software.tar.gz -C /opt/slurm-factory && \
    rm -rf /tmp/slurm-tarball

ENV MODULEPATH=/opt/slurm-factory/assets/modules:$MODULEPATH \
    SLURM_INSTALL_PREFIX=/opt/slurm-factory/view

RUN mkdir -p /etc/slurm /var/spool/slurm/ctld /var/spool/slurm/d /var/log/slurm && \
    cat >/etc/slurm/slurm.conf <<'SLURMCONF'
ClusterName=tarball-demo
SlurmctldHost=localhost
AuthType=auth/slurm
AuthInfo=/etc/slurm/slurm.key
SlurmUser=root
SlurmdUser=root
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log
ProctrackType=proctrack/linuxproc
TaskPlugin=task/none
PluginDir=/opt/slurm-factory/view/lib/slurm
NodeName=localhost CPUs=4 State=UNKNOWN
PartitionName=debug Nodes=localhost Default=YES MaxTime=INFINITE State=UP
SLURMCONF

RUN dd if=/dev/urandom bs=1 count=1024 of=/etc/slurm/slurm.key 2>/dev/null && \
    chmod 600 /etc/slurm/slurm.key

CMD ["/opt/slurm-factory/view/bin/sinfo"]
```

## Next Steps

- Replace the sample `slurm.conf` with your production configuration (see [`deployment.md`](./deployment.md)).
- Convert the one-shot commands into systemd units provided in `/opt/slurm-factory/etc/systemd/`.
- Mirror the tarball to your internal artifact repository if required.
- Combine with the [buildcache mirror documentation](./slurm-factory-spack-build-cache.md) when you need to build fresh tarballs for additional architectures.

