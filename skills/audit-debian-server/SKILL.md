---
name: audit-debian-server
description: >-
  Audit, harden, and monitor Debian or Ubuntu application servers. TRIGGER on
  assessing server exposure, SSH, firewall, VPN, service security, patching,
  or host monitoring. SKIP application development and non-Debian systems.
---

# Debian Server Security Audit

Assess read-only first. Preserve the current SSH path and application
availability. Do not change packages, users, SSH, firewall, routing,
WireGuard, services, configuration, or reboot state until the user approves a
concrete remediation plan.

## Collect evidence

Establish the environment, Debian/Ubuntu release, hosting topology, intended
public services, and management path. Run
`scripts/collect-audit.sh` as the normal administrator. It creates an
owner-readable local evidence directory without collecting private keys,
secret values, or full service configuration. Request sudo only for specific
read-only evidence that is otherwise unavailable.

Read [audit-checklist.md](references/audit-checklist.md) to interpret host and
network evidence. Read [service-guidance.md](references/service-guidance.md)
when web services, containers, databases, or WireGuard are in scope. Keep
artifacts, addresses, hostnames, logs, and configuration on the host unless
the user authorizes sharing them.

Corroborate local listeners and firewall state with provider firewalls, load
balancers, DNS, and CDN configuration. Treat scanner output as a lead and
confirm intended exposure before calling it a vulnerability.

## Report and plan

Separate facts, uncertainty, risk, and recommendations. Report:

- scope, access assumptions, evidence gaps, and an exposure map;
- findings ordered Critical, High, Medium, then Low;
- exact prerequisites, affected files/services, connection impact, reboot
  needs, validation, and rollback for each proposed change;
- monitoring coverage, alert tests, and a short 7/30/90-day follow-up plan.

State plainly when no live scan, provider-perimeter review, backup restore, or
external test was performed. Never print credentials, private keys, tokens,
secret-bearing environment variables, or complete sensitive configuration.

## Apply approved remediation

For network or SSH work, require two recovery paths, such as the existing SSH
session plus a provider console. Keep the session open, schedule rollback
where practical, validate syntax before reload, and test a fresh SSH login
before closing it. Change firewall, SSH, routing, and WireGuard policy in
separate verified steps.

Back up each changed file with ownership and mode preserved. Prefer supported
drop-ins and distribution packages. Validate configuration before activation,
reload where safe, and immediately verify service and connection health. Stop
and recover on failed validation, unexpected routing, application errors, or
lost access.

Do not disable authentication methods, root login, IPv6, forwarding,
unattended upgrades, services, or ports from a generic baseline; confirm they
are unnecessary here. Coordinate WireGuard key or `AllowedIPs` changes with
peers.

## Monitoring

Start with systemd failures, journal health, resource pressure, time sync,
storage health, backup jobs, and isolated restore tests. Size any added system
to the existing stack. Cover reachability, authentication anomalies, patches,
certificate expiry, HTTP health, services, disk/inodes, and expected
WireGuard activity. Confirm receiver ownership, privacy, retention, severity
routing, and a reversible alert test before enabling notifications.
