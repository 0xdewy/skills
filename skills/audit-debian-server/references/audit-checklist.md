# Audit checklist

Use this after collecting evidence. Confirm intended exposure before flagging a listener.

## Platform and patching

- Confirm supported release, enabled repositories, kernel age, reboot requirement, and package update policy.
- Check unattended-upgrades policy, timer status, held packages, and security update failures. Distinguish a missing update from an intentionally pinned package.
- Review time synchronization, persistent journal capacity, disk/inode pressure, failed units, and unexpected scheduled jobs.

## Identity and remote access

- Inventory interactive users, UID 0 accounts, authorized admin paths, sudo rules, SSH effective settings, and ownership/modes of SSH configuration and authorized keys.
- Treat SSH changes as high risk. Prefer named admin accounts, least privilege, key-based authentication, modern algorithms supported by the installed OpenSSH version, and rate limiting/abuse controls appropriate to the deployment.
- Do not recommend root/password-login removal until a fresh non-root key login and console/bastion recovery are proven.

## Network controls

- Compare `ss` listeners, bind addresses, systemd socket units, reverse-proxy configuration, host firewall, cloud firewall/security groups, and load balancer/CDN configuration.
- Check IPv4 and IPv6 independently. Review forwarding and source-routing settings in context; forwarding can be required for WireGuard gateways and containers.
- Use default-deny ingress only after documenting every required management, application, health-check, VPN, and egress dependency. Keep stateful return traffic and necessary ICMP/ICMPv6 behavior.

## Application and data plane

- Identify web server, runtime, process manager, containers, databases, queues, object storage access, and scheduled jobs. Verify each runs under the least-privileged viable identity, has narrow filesystem access, and does not expose an admin/debug endpoint publicly.
- Review TLS certificate chain/expiry, HTTP-to-HTTPS behavior, Host handling, security headers appropriate to the application, request-size/time limits, upload controls, logs, and rate limiting. Do not enable headers blindly when they can break application behavior.
- Check secret handling by location and permissions only; never collect or echo secret values. Ensure backups are encrypted, access-controlled, monitored, and restore-tested.

## Detection and assurance

- Review authentication and web error logs for suspicious patterns; preserve raw evidence locally. Consider distribution-supported integrity, vulnerability, and log-analysis tools only with approval.
- Verify backup success is not a restore guarantee: perform or schedule an isolated restore test.
- Scope external scanning explicitly. It can affect production services and requires permission for target, source, timing, and rate.
