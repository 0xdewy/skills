#!/usr/bin/env bash
# Read-only local evidence collection for a Debian/Ubuntu security review.
set -euo pipefail

if [[ ${EUID} -eq 0 ]]; then
  echo 'Run as the normal admin user; use sudo only for individual read-only follow-up commands.' >&2
  exit 2
fi

out_dir=${1:-"./server-audit-$(hostname -s 2>/dev/null || echo host)-$(date -u +%Y%m%dT%H%M%SZ)"}
umask 077
mkdir -p -- "$out_dir"

capture() {
  local file=$1
  shift
  { printf '$'; printf ' %q' "$@"; printf '\n\n'; "$@"; } >"$out_dir/$file" 2>&1 || true
}

capture os-release.txt cat /etc/os-release
capture kernel.txt uname -a
capture uptime.txt uptime
capture listening-sockets.txt ss -lntup
capture routes.txt ip route show
capture addresses.txt ip -brief address show
capture firewall-nft.txt nft list ruleset
capture firewall-ufw.txt ufw status verbose
capture firewall-iptables.txt iptables-save
capture services-enabled.txt systemctl list-unit-files --state=enabled
capture services-failed.txt systemctl --failed --no-pager
capture processes.txt ps -eo user,pid,ppid,stat,etime,comm
capture packages-upgradable.txt apt list --upgradable
capture automatic-updates.txt systemctl status apt-daily.timer apt-daily-upgrade.timer --no-pager
capture accounts.txt getent passwd
capture sudoers-metadata.txt find /etc/sudoers.d -maxdepth 1 -type f -printf '%m %u %g %p\n'
capture sshd-effective.txt sshd -T
capture sshd-config-metadata.txt find /etc/ssh/sshd_config.d -maxdepth 1 -type f -printf '%m %u %g %p\n'
capture filesystem.txt df -hT
capture inodes.txt df -hi
capture mounts.txt findmnt
capture timers.txt systemctl list-timers --all --no-pager
capture time-sync.txt timedatectl status
capture journal.txt journalctl --disk-usage
capture certs.txt find /etc/letsencrypt/live -maxdepth 2 -name cert.pem -print
capture wireguard-status.txt wg show
capture wireguard-links.txt ip -brief link show type wireguard
capture docker.txt docker ps --format '{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}'
capture podman.txt podman ps --format '{{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}'
capture fail2ban.txt fail2ban-client status

printf 'Created %s\n' "$out_dir"
printf 'Review files locally before sharing; they may contain usernames, public addresses, and service names.\n'
