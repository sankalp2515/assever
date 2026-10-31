#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io python3 python3-yaml curl ca-certificates
systemctl enable --now docker
mkdir -p /usr/local/lib/docker/cli-plugins /srv/assever /opt/assever
if [ ! -x /usr/local/lib/docker/cli-plugins/docker-compose ]; then
  mkdir -p /tmp/assever-compose
  curl -fsSL https://github.com/docker/compose/releases/download/v2.40.3/docker-compose-linux-x86_64 -o /tmp/assever-compose/docker-compose-linux-x86_64
  curl -fsSL https://github.com/docker/compose/releases/download/v2.40.3/docker-compose-linux-x86_64.sha256 -o /tmp/assever-compose/checksum
  (cd /tmp/assever-compose && sha256sum -c checksum)
  install -m 755 /tmp/assever-compose/docker-compose-linux-x86_64 /usr/local/lib/docker/cli-plugins/docker-compose
fi
device=/dev/disk/by-id/google-assever-data
if ! blkid "$device"; then mkfs.ext4 -m 0 "$device"; fi
mountpoint -q /srv/assever || mount "$device" /srv/assever
uuid=$(blkid -s UUID -o value "$device")
grep -q "$uuid" /etc/fstab || printf 'UUID=%s /srv/assever ext4 defaults,nofail 0 2\n' "$uuid" >> /etc/fstab
mkdir -p /srv/assever/postgres /srv/assever/gateway /srv/assever/evidence
chown 1000:1000 /srv/assever/gateway /srv/assever/evidence
chmod 700 /opt/assever
touch /opt/assever/startup-ready
