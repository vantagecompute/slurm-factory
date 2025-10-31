#!/bin/bash
# Slurm Installation and Configuration Script
# This script sets up the Slurm workload manager filesystem and configuration

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
FULL_INIT=false
INIT_ONLY=false
START_SERVICES=false
HEAD_NODE_INIT=false
CLUSTER_NAME="cluster"
ORG_ID=""
SSSD_BINDER_PASSWORD=""
LDAP_URI=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --full-init)
            FULL_INIT=true
            shift
            ;;
        --start-services)
            START_SERVICES=true
            shift
            ;;
        --init-only)
            INIT_ONLY=true
            shift
            ;;
        --head-node-init)
            HEAD_NODE_INIT=true
            shift
            ;;
        --cluster-name)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --org-id)
            ORG_ID="$2"
            shift 2
            ;;
        --sssd-binder-password)
            SSSD_BINDER_PASSWORD="$2"
            shift 2
            ;;
        --ldap-uri)
            LDAP_URI="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full-init|--init-only|--head-node-init] [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full-init                Install software and automatically configure/start services"
            echo "  --init-only                Only configure and start services (skip installation)"
            echo "  --head-node-init           Install head node dependencies (users, packages)"
            echo "  --cluster-name NAME        Set cluster name (default: cluster)"
            echo "  --org-id ID                Organization ID for SSSD configuration"
            echo "  --sssd-binder-password PW  SSSD binder password"
            echo "  --ldap-uri URI             LDAP URI for SSSD"
            exit 1
            ;;
    esac
done

echo "=== Slurm Installation Script ==="
if [[ "$INIT_ONLY" == "true" ]]; then
    echo "Mode: Initialization only (skipping installation)"
    echo "This script will:"
    echo "  1. Auto-configure hardware parameters"
    echo "  2. Enable and start Slurm services"
else
    echo "This script will:"
    echo "  1. Create necessary directories"
    echo "  2. Install configuration files"
    echo "  3. Install systemd service files"
    echo "  4. Set up proper permissions"
    echo "  5. Download and install Slurm software"
    if [[ "$FULL_INIT" == "true" ]]; then
        echo "  6. Auto-configure hardware parameters"
        echo "  7. Enable and start Slurm services"
    fi
fi
echo

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "Error: This script must be run as root" 
   exit 1
fi

# Head Node Initialization
if [[ "$HEAD_NODE_INIT" == "true" ]]; then
    echo "=== Head Node Initialization ==="
    echo "Setting up system users and installing head node packages..."
    
    # Create system users
    echo "Creating system users..."
    
    # Create slurm user if it doesn't exist
    if ! id slurm &>/dev/null; then
        echo "Creating slurm user (uid 64031)..."
        useradd --system --uid 64031 --no-create-home --shell /usr/sbin/nologin slurm
    else
        echo "slurm user already exists"
    fi
    
    # Create slurmrestd user if it doesn't exist
    if ! id slurmrestd &>/dev/null; then
        echo "Creating slurmrestd user (uid 64032)..."
        useradd --system --uid 64032 --no-create-home --shell /usr/sbin/nologin slurmrestd
    else
        echo "slurmrestd user already exists"
    fi
    
    # Create ubuntu user if it doesn't exist
    if ! id ubuntu &>/dev/null; then
        echo "Creating ubuntu user with sudo access..."
        useradd -m -s /bin/bash ubuntu
        usermod -aG sudo ubuntu
        echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/ubuntu
        chmod 0440 /etc/sudoers.d/ubuntu
    else
        echo "ubuntu user already exists"
    fi
    
    # Add Apptainer PPA
    echo "Adding Apptainer PPA..."
    apt-get update
    apt-get install -y software-properties-common
    
    # Add GPG key for Apptainer PPA
    echo "Adding Apptainer GPG key..."
    cat > /tmp/apptainer-key.asc << 'EOF'
-----BEGIN PGP PUBLIC KEY BLOCK-----
Comment: Hostname:
Version: Hockeypuck 2.1.0-223-gdc2762b

xsFNBGPKLe0BEADKAHtUqLFryPhZ3m6uwuIQvwUr4US17QggRrOaS+jAb6e0P8kN
1clzJDuh3C6GnxEZKiTW3aZpcrW/n39qO263OMoUZhm1AliqiViJgthnqYGSbMgZ
/OB6ToQeHydZ+MgI/jpdAyYSI4Tf4SVPRbOafLvnUW5g/vJLMzgTAxyyWEjvH9Lx
yjOAXpxubz0Wu2xcoefN0mKCpaPsa9Y8xmog1lsylU+H/4BX6yAG7zt5hIvadc9Z
Y/vkDLh8kNaEtkXmmnTqGOsLgH6Nc5dnslR6Gwq966EC2Jbw0WbE50pi4g21s6Wi
wdU27/XprunXhhLdv6PYUaqdXxPRdBh+9u0LmNZsAyUxT6EgN05TAWFtaMOz7I3B
V6IpHuLqmIcnqulHrLi+0D/aiCv53WEZrBRmDBGX7p52lcyS+Q+LFf0+iYeY7pRG
fPXboBDr+6DelkYFIxam06purSGR3T9RJyrMP7qMWiInWxcxBoCMNfy8VudP0DAy
r2yXmHZbgSGjfJey03dnNwQH7huBcQ1VLEqtL+bjn3HubmYK87FltX7xomETFqcl
QmiT+WBttFRGtO6SFHHiBXOXUn0ihwabtr6gRKeJssCnFS3Y46RDv4z3Je92roLt
TPY8F9CgZrGiAoKq530BzEhJB6vfW3faRnLKdLePX/LToCP0g2t2jKwkzQARAQAB
zRtMYXVuY2hwYWQgUFBBIGZvciBBcHB0YWluZXLCwY4EEwEKADgWIQT2sPUZPU8z
Ae9JH/Cv42U0/GIYrgUCY8ot7QIbAwULCQgHAgYVCgkICwIEFgIDAQIeAQIXgAAK
CRCv42U0/GIYrut4EAC06vTJP2wgnh3BIZ3n2HKaSp4QsuYKS7F7UQJ5Yt+PpnKn
Pgjq3R4fYzOHyASv+TCj9QkMaeqWGWb6Zw0n47EtrCW9U5099Vdk2L42KjrqZLiW
qQ11hwWXUlc1ZYSOb0J4WTumgO6MrUCFkmNrbRE7yB42hxr/AU/XNM38YjN2NyOK
2gvORRKFwlLKrjE+70HmoCW09Yk64BZl1eCubM/qy5tKzSlC910uz87FvZmrGKKF
rXa2HGlO4O3Ty7bMSeRKl9m1OYuffAXNwp3/Vale9eDHOeq58nn7wU9pSosmqrXb
SLOwqQylc1YoLZMj+Xjx644xm5e2bhyD00WiHeqHmvlfQQWCWaPt4i4K0nJuYXwm
BCA6YUgSfDZJfg/FxJdU7ero5F9st2GK4WDBiz+1Eftw6Ik/WnMDSxXaZ8pwnd9N
+aAEc/QKP5e8kjxJMC9kfvXGUVzZuMbkUV+PycZhUWl4Aelua91lnTicVYfpuVCC
GqY0StWQeOxLJneI+1FqLFoBOZghzoTY5AYCp99RjKqQvY1vF4uErltmNeN1vtBm
CZyDOLQuQfqWWAunUwXVuxMJIENSVeLXunhu9ac24Vnf2rFqH4XVMDxiKc6+sv+v
fKpamSQOUSmfWJTnry/LiYbspi1OB2x3GQk3/4ANw0S4L83A6oXHUMg8x7/sZw==
=E71P
-----END PGP PUBLIC KEY BLOCK-----
EOF
    gpg --dearmor < /tmp/apptainer-key.asc > /usr/share/keyrings/apptainer-archive-keyring.gpg
    rm -f /tmp/apptainer-key.asc
    
    # Add Apptainer repository
    echo "deb [signed-by=/usr/share/keyrings/apptainer-archive-keyring.gpg] https://ppa.launchpadcontent.net/apptainer/ppa/ubuntu $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/apptainer.list
    
    # Update package lists
    echo "Updating package lists..."
    apt-get update
    
    # Install packages
    echo "Installing head node packages..."
    apt-get install -y \
        libpmix-dev \
        openmpi-bin \
        parallel \
        mysql-server \
        libedit2 \
        apptainer-suid \
        influxdb \
        influxdb-client \
        wget \
        autossh \
        lmod \
        oddjob-mkhomedir \
        ldap-utils \
        dbus-daemon \
        authselect \
        sssd \
        sssd-ad \
        sssd-ldap \
        sssd-dbus \
        sssd-tools \
        libpam-sss \
        libnss-sss
    
    echo "Head node initialization complete!"
    echo
fi

# Skip installation if --init-only is specified
if [[ "$INIT_ONLY" == "true" ]]; then
    echo "Skipping installation steps (--init-only mode)"
    echo
    # Jump directly to initialization
else
    # Perform full installation
    # Check if slurm user exists
    if ! id slurm &>/dev/null; then
        echo "Error: slurm user does not exist. Please create it first:"
        echo "  useradd --system --uid 64031 --no-create-home --shell /usr/sbin/nologin slurm"
        exit 1
    fi

    # Check if slurmrestd user exists
    if ! id slurmrestd &>/dev/null; then
        echo "Error: slurmrestd user does not exist. Please create it first:"
        echo "  useradd --system --uid 64032 --no-create-home --shell /usr/sbin/nologin slurmrestd"
        exit 1
        fi

echo "=== Creating Slurm directories ==="
mkdir -p /etc/slurm
mkdir -p /opt/slurm
mkdir -p /var/lib/slurm
mkdir -p /var/lib/slurm/checkpoint
mkdir -p /var/lib/slurm/slurmd
mkdir -p /var/lib/slurm/slurmctld
mkdir -p /var/log/slurm
mkdir -p /var/spool/slurmd

echo "=== Installing Slurm configuration files ==="
install -m 0644 -o root -g root "${SCRIPT_DIR}/slurm/oci.conf" /etc/slurm/oci.conf
install -m 0644 -o root -g root "${SCRIPT_DIR}/slurm/cgroup.conf" /etc/slurm/cgroup.conf
install -m 0644 -o root -g root "${SCRIPT_DIR}/slurm/slurm.conf" /etc/slurm/slurm.conf
install -m 0600 -o root -g root "${SCRIPT_DIR}/slurm/slurmdbd.conf" /etc/slurm/slurmdbd.conf
install -m 0644 -o root -g root "${SCRIPT_DIR}/slurm/acct_gather.conf" /etc/slurm/acct_gather.conf

echo "=== Installing systemd service files ==="
install -m 0644 -o root -g root "${SCRIPT_DIR}/systemd/slurmctld.service" /usr/lib/systemd/system/slurmctld.service
install -m 0644 -o root -g root "${SCRIPT_DIR}/systemd/slurmd.service" /usr/lib/systemd/system/slurmd.service
install -m 0644 -o root -g root "${SCRIPT_DIR}/systemd/slurmdbd.service" /usr/lib/systemd/system/slurmdbd.service
install -m 0644 -o root -g root "${SCRIPT_DIR}/systemd/slurmrestd.service" /usr/lib/systemd/system/slurmrestd.service

echo "=== Installing default environment files ==="
mkdir -p /etc/default
install -m 0644 -o root -g root "${SCRIPT_DIR}/defaults/slurmd" /etc/default/slurmd
install -m 0644 -o root -g root "${SCRIPT_DIR}/defaults/slurmctld" /etc/default/slurmctld
install -m 0644 -o root -g root "${SCRIPT_DIR}/defaults/slurmdbd" /etc/default/slurmdbd
install -m 0644 -o root -g root "${SCRIPT_DIR}/defaults/slurmrestd" /etc/default/slurmrestd

echo "=== Installing tmpfiles.d configuration ==="
mkdir -p /etc/tmpfiles.d
install -m 0644 -o root -g root "${SCRIPT_DIR}/tmpfiles.d/slurmctld.conf" /etc/tmpfiles.d/slurmctld.conf
install -m 0644 -o root -g root "${SCRIPT_DIR}/tmpfiles.d/slurmd.conf" /etc/tmpfiles.d/slurmd.conf
install -m 0644 -o root -g root "${SCRIPT_DIR}/tmpfiles.d/slurmdbd.conf" /etc/tmpfiles.d/slurmdbd.conf
install -m 0644 -o root -g root "${SCRIPT_DIR}/tmpfiles.d/slurmrestd.conf" /etc/tmpfiles.d/slurmrestd.conf

echo "=== Installing profile.d script for Lmod ==="
mkdir -p /etc/profile.d
install -m 0644 -o root -g root "${SCRIPT_DIR}/profile.d/z00_lmod.sh" /etc/profile.d/z00_lmod.sh

echo "=== Generating Slurm authentication key ==="
if [[ ! -f /etc/slurm/slurm.key ]]; then
    openssl rand 2048 | base64 | tr -d '\n' > /etc/slurm/slurm.key
    chmod 600 /etc/slurm/slurm.key
    chown slurm:slurm /etc/slurm/slurm.key
    echo "Generated new slurm.key"
else
    echo "slurm.key already exists, skipping"
fi

echo "=== Generating JWT RS256 key ==="
if [[ ! -f /etc/slurm/jwt_hs256.key ]]; then
    openssl genrsa -out /etc/slurm/jwt_hs256.key 2048
    chmod 600 /etc/slurm/jwt_hs256.key
    chown slurm:slurm /etc/slurm/jwt_hs256.key
    echo "Generated new jwt_hs256.key"
else
    echo "jwt_hs256.key already exists, skipping"
fi

echo "=== Setting Slurm directory permissions ==="
chown -R slurm:slurm /var/log/slurm
chown -R slurm:slurm /var/lib/slurm
chown slurm:slurm /etc/slurm/slurmdbd.conf
chown slurm:slurm /etc/slurm/slurm.conf


echo "=== Installing Slurm software ==="
# Check if Slurm binaries already exist in the expected location
if [[ -d /opt/slurm/view/bin ]] && [[ -f /opt/slurm/view/bin/sinfo ]]; then
    echo "Slurm software already present at /opt/slurm/view"
else
    echo "Downloading and extracting Slurm software"
    mkdir -p /opt/slurm
    wget -qO- https://vantage-public-assets.s3.us-west-2.amazonaws.com/slurm/25.05/slurm-latest.tar.gz | \
        tar --no-same-owner --no-same-permissions --touch -xz -C /opt/slurm
    echo "Slurm software installed to /opt/slurm/view"
fi

echo "=== Installing Slurm Lmod module ==="
if [[ -d /usr/share/lmod/lmod/modulefiles ]]; then
    # Module files should be in the extracted tarball
    if [[ -d "$(dirname "$SCRIPT_DIR")/modules/slurm" ]]; then
        echo "Installing Lmod module from extracted tarball"
        mkdir -p /usr/share/lmod/lmod/modulefiles/slurm
        cp "$(dirname "$SCRIPT_DIR")/modules/slurm/"*.lua /usr/share/lmod/lmod/modulefiles/slurm/
        echo "Slurm Lmod module installed from tarball"
    else
        echo "Error: Module files not found in tarball at $(dirname "$SCRIPT_DIR")/modules/slurm"
        exit 1
    fi
else
    echo "Warning: Lmod modulefiles directory not found, skipping module installation"
fi

echo "=== Creating Slurm command wrapper scripts ==="
for i in /opt/slurm/view/bin/sacct \
  /opt/slurm/view/bin/sacctmgr \
  /opt/slurm/view/bin/salloc \
  /opt/slurm/view/bin/sattach \
  /opt/slurm/view/bin/sbang \
  /opt/slurm/view/bin/sbatch \
  /opt/slurm/view/bin/sbcast \
  /opt/slurm/view/bin/scancel \
  /opt/slurm/view/bin/scontrol \
  /opt/slurm/view/bin/scrontab \
  /opt/slurm/view/bin/sdiag \
  /opt/slurm/view/bin/sh5util \
  /opt/slurm/view/bin/sinfo \
  /opt/slurm/view/bin/sprio \
  /opt/slurm/view/bin/squeue \
  /opt/slurm/view/bin/sreport \
  /opt/slurm/view/bin/srun \
  /opt/slurm/view/bin/sshare \
  /opt/slurm/view/bin/sstat \
  /opt/slurm/view/bin/strigger \
  /opt/slurm/view/sbin/slurmctld \
  /opt/slurm/view/sbin/slurmd \
  /opt/slurm/view/sbin/slurmdbd \
  /opt/slurm/view/sbin/slurmrestd \
  /opt/slurm/view/sbin/slurmstepd; do

  if [[ ! -f "$i" ]]; then
    echo "Warning: $i not found, skipping wrapper creation"
    continue
  fi

  BASENAME=$(basename "$i")
  
  case "$i" in
    *sbin*)
      TARGET_DIR="/usr/sbin"
      ;;
    *)
      TARGET_DIR="/usr/bin"
      ;;
  esac
  
  echo "Creating wrapper for $BASENAME in $TARGET_DIR"
  
  # Create wrapper script that sources z00_lmod.sh (which loads slurm module) before executing
  cat > "${TARGET_DIR}/${BASENAME}" << WRAPPER_EOF
#!/bin/bash
source /etc/profile.d/z00_lmod.sh
exec $i "\$@"
WRAPPER_EOF
  
  # Make wrapper executable
  chmod +x "${TARGET_DIR}/${BASENAME}"

done

echo "=== Creating runtime directories ==="
systemd-tmpfiles --create /etc/tmpfiles.d/slurmctld.conf
systemd-tmpfiles --create /etc/tmpfiles.d/slurmd.conf
systemd-tmpfiles --create /etc/tmpfiles.d/slurmdbd.conf
systemd-tmpfiles --create /etc/tmpfiles.d/slurmrestd.conf

echo "=== Reloading systemd daemon ==="
systemctl daemon-reload

fi  # End of installation section

# SSSD configuration - runs before Slurm initialization if parameters provided
if [[ -n "$ORG_ID" ]] && [[ -n "$SSSD_BINDER_PASSWORD" ]] && [[ -n "$LDAP_URI" ]]; then
    echo
    echo "=== Configuring SSSD ==="
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cp "$SCRIPT_DIR/sssd/sssd.conf" /etc/sssd/sssd.conf
    chmod 600 /etc/sssd/sssd.conf
    chown root:root /etc/sssd/sssd.conf
    echo "  Org ID: $ORG_ID"
    echo "  LDAP URI: $LDAP_URI"
    echo "  Setting binder password..."

    sed -i "s|@ORG_ID@|$ORG_ID|g" /etc/sssd/sssd.conf
    sed -i "s|@SSSD_BINDER_PASSWORD@|$SSSD_BINDER_PASSWORD|g" /etc/sssd/sssd.conf
    sed -i "s|@LDAP_URI@|$LDAP_URI|g" /etc/sssd/sssd.conf

    echo "  ✓ SSSD configuration updated"

    if systemctl is-active --quiet sssd; then
        echo "  Restarting SSSD service..."
        systemctl restart sssd
        echo "  ✓ SSSD restarted"
    elif systemctl is-enabled --quiet sssd; then
        echo "  Starting SSSD service..."
        systemctl start sssd
        echo "  ✓ SSSD started"
    else
        echo "  Enabling and starting SSSD service..."
        systemctl enable --now sssd
        echo "  ✓ SSSD enabled and started"
    fi
elif [[ -n "$ORG_ID" ]] || [[ -n "$SSSD_BINDER_PASSWORD" ]] || [[ -n "$LDAP_URI" ]]; then
    echo
    echo "Warning: Partial SSSD configuration provided. All three parameters are required:"
    echo "  --org-id, --sssd-binder-password, --ldap-uri"
    echo "Skipping SSSD configuration."
fi

# Initialization section - runs for both --full-init and --init-only
if [[ "$FULL_INIT" == "true" ]] || [[ "$INIT_ONLY" == "true" ]]; then
    echo
    echo "=== Auto-configuring Slurm ==="
    
    # Check for required commands
    if ! command -v jq &> /dev/null; then
        echo "Error: jq is required for --full-init but not installed"
        exit 1
    fi
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cp "${SCRIPT_DIR}/slurm/slurm.conf" /etc/slurm/slurm.conf
    cp "${SCRIPT_DIR}/slurm/slurmdbd.conf" /etc/slurm/slurmdbd.conf
    
    echo "=== Detecting hardware configuration ==="
    cpu_info=$(lscpu -J | jq)
    echo "$cpu_info"
    CPUs=$(echo "$cpu_info" | jq -r '.lscpu | .[] | select(.field == "CPU(s):") | .data')
    echo "  CPUs: $CPUs"
    sed -i "s|@CPUs@|$CPUs|g" /etc/slurm/slurm.conf
    
    THREADS_PER_CORE=$(echo "$cpu_info" | jq -r '.lscpu | .[] | select(.field == "Thread(s) per core:") | .data')
    echo "  Threads per core: $THREADS_PER_CORE"
    sed -i "s|@THREADS_PER_CORE@|$THREADS_PER_CORE|g" /etc/slurm/slurm.conf
    
    CORES_PER_SOCKET=$(echo "$cpu_info" | jq -r '.lscpu | .[] | select(.field == "Core(s) per socket:") | .data')
    echo "  Cores per socket: $CORES_PER_SOCKET"
    sed -i "s|@CORES_PER_SOCKET@|$CORES_PER_SOCKET|g" /etc/slurm/slurm.conf
    
    SOCKETS=$(echo "$cpu_info" | jq -r '.lscpu | .[] | select(.field == "Socket(s):") | .data')
    echo "  Sockets: $SOCKETS"
    sed -i "s|@SOCKETS@|$SOCKETS|g" /etc/slurm/slurm.conf
    
    REAL_MEMORY=$(free -m | grep -oP '\d+' | head -n 1)
    echo "  Real memory: ${REAL_MEMORY}MB"
    sed -i "s|@REAL_MEMORY@|$REAL_MEMORY|g" /etc/slurm/slurm.conf
    
    echo "=== Configuring hostnames and cluster name ==="
    HEADNODE_HOSTNAME=$(hostname)
    HEADNODE_ADDRESS=$(hostname -I | awk '{print $1}')
    
    echo "  Cluster name: $CLUSTER_NAME"
    echo "  Headnode hostname: $HEADNODE_HOSTNAME"
    echo "  Headnode address: $HEADNODE_ADDRESS"
    
    sed -i "s|@HEADNODE_HOSTNAME@|$HEADNODE_HOSTNAME|g" /etc/slurm/slurmdbd.conf
    sed -i "s|@HEADNODE_ADDRESS@|$HEADNODE_ADDRESS|g" /etc/slurm/slurm.conf
    sed -i "s|@HEADNODE_HOSTNAME@|$HEADNODE_HOSTNAME|g" /etc/slurm/slurm.conf
    sed -i "s|^ClusterName=.*|ClusterName=$CLUSTER_NAME|g" /etc/slurm/slurm.conf
    sed -i "s|@CLUSTER_NAME@|$CLUSTER_NAME|g" /etc/slurm/slurm.conf
    
    echo "=== Setting up Slurm database ==="
    cp "${SCRIPT_DIR}/mysql/slurm.cnf" /etc/mysql/mysql.conf.d/slurm.cnf

    systemctl stop mysql.service
    systemctl enable --now mysql.service
    
    # Wait for MySQL to be ready
    sleep 5

    mysql --socket=/var/run/mysqld/mysqld.sock << 'END_SQL'
CREATE USER IF NOT EXISTS 'slurm'@'localhost' IDENTIFIED BY 'rats';
CREATE DATABASE IF NOT EXISTS slurm DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON slurm.* TO 'slurm'@'localhost';
END_SQL
     
    # Configure InfluxDB
    systemctl stop influxdb.service
    systemctl enable --now influxdb.service
    sleep 5
    influx -execute "CREATE USER slurm WITH PASSWORD 'rats'"
    influx -execute 'CREATE DATABASE "slurm-job-metrics"'
    influx -execute 'GRANT ALL ON "slurm-job-metrics" TO "slurm"'
    influx -execute 'CREATE RETENTION POLICY "three_days" ON "slurm-job-metrics" DURATION 3d REPLICATION 1 DEFAULT'
    #influx -execute 'CREATE CONTINUOUS QUERY "slurm_job_metrics" ON "slurm-job-metrics" BEGIN SELECT mean("value") INTO "slurm-job-metrics"."three_days"."mean_value" FROM "slurm-job-metrics" GROUP BY time(1h) END'
    if [ $START_SERVICES == "true" ]; then
        echo "=== Enabling and starting Slurm services ==="
        systemctl enable slurmdbd
        systemctl start slurmdbd
        echo "  ✓ slurmdbd enabled and started"
    
        systemctl enable slurmctld
        systemctl start slurmctld
        echo "  ✓ slurmctld enabled and started"
    
        systemctl enable slurmd
        systemctl start slurmd
        echo "  ✓ slurmd enabled and started"

        systemctl enable slurmrestd
        systemctl start slurmrestd
        echo "  ✓ slurmrestd enabled and started"

        echo "=== Verifying services ==="
        sleep 2  # Give services a moment to start
        systemctl status slurmdbd --no-pager || true
        systemctl status slurmctld --no-pager || true
        systemctl status slurmd --no-pager || true
        systemctl status slurmrestd --no-pager || true
    
        echo
        echo "=== Full initialization complete! ==="
        echo "Slurm is now configured and running."
        echo
        echo "To verify cluster status, run:"
        echo "  sinfo"
        echo "  scontrol show nodes"
    fi
    exit 0
fi

# Only show manual next steps if neither --full-init nor --init-only was used
echo
echo "=== Slurm installation complete! ==="
echo
echo "Next steps:"
echo "  1. Edit /etc/slurm/slurm.conf to replace @VARIABLES@ with actual values:"
echo "     - @CLUSTER_NAME@"
echo "     - @HEADNODE_HOSTNAME@"
echo "     - @HEADNODE_ADDRESS@"
echo "     - @CPUs@, @THREADS_PER_CORE@, @CORES_PER_SOCKET@, @SOCKETS@, @REAL_MEMORY@"
echo
echo "  2. Edit /etc/slurm/slurmdbd.conf to replace @HEADNODE_HOSTNAME@"
echo
echo "  3. Ensure MySQL is configured and the slurm database exists"
echo
echo "  4. Enable and start Slurm services:"
echo "     systemctl enable --now slurmdbd"
echo "     systemctl enable --now slurmctld"
echo "     systemctl enable --now slurmd"
echo
echo "  5. Verify services are running:"
echo "     systemctl status slurmdbd slurmctld slurmd"
echo
echo "Alternatively, run this script with --full-init to automatically configure and start:"
echo "  $0 --full-init [--cluster-name YOURCLUSTER]"
echo
echo "Or use --init-only if Slurm is already installed:"
echo "  $0 --init-only [--cluster-name YOURCLUSTER]"
echo
