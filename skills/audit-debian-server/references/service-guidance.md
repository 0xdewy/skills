# Service guidance

## WireGuard

- Record interface addresses, UDP listen ports, peer public-key fingerprints, `AllowedIPs`, routes, forwarding/NAT dependencies, handshake age, and expected traffic direction. Do not read or disclose private keys or full configuration files without a specific need and approval.
- Treat `AllowedIPs` as routing and authorization policy. Detect overlapping routes, overly broad prefixes, stale peers, unexpected endpoint changes, absent kill-switch policy where required, and missing persistent keepalive only when NAT traversal needs it.
- Restrict UDP exposure at the host and provider perimeter to the required port; source restriction is optional and can break roaming peers. Confirm DNS, MTU, and return routing before changing policies.
- Monitor interface state, peer handshake age relative to expected activity, transfer changes, service/unit failures, and route drift. An idle peer is not automatically a fault.

## Web apps and reverse proxies

- Map public hostnames and proxies to upstreams. Bind app/admin/debug ports to loopback or private networks unless public exposure is intentional.
- Test proxy syntax before reload, preserve a working configuration copy, and use health endpoints that do not disclose sensitive data. Confirm rate limits and request/body/time limits match the app.
- Monitor certificate expiry, HTTPS success and latency, expected status/body marker, upstream availability, error rate, process restarts, and disk capacity for logs/uploads.

## Containers and databases

- Inventory published ports, privileged containers, host namespaces, Docker socket mounts, image provenance/update process, runtime users, and persistent-volume backups.
- Keep databases bound to private/loopback networks unless a documented client network needs access. Require encrypted transport and least-privilege database roles where supported. Test restores, not merely backup completion.
