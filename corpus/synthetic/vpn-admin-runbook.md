+++
title = "VPN administrator runbook"
classification = "it_restricted"
synthetic = true
+++

# VPN administrator runbook

## Certificate renewal procedure

This runbook is for authorized network administrators who maintain the remote access VPN service. It is not an end-user troubleshooting guide. Before a planned certificate change, verify the maintenance approval, change window, service owner, and rollback contact. Confirm that the target gateway is `vpn.demo.local` and that the certificate inventory identifies the correct service entry.

Review the certificate subject, issuing authority, validity period, and intended server authentication usage. Compare the certificate fingerprint with the value recorded in the approved change ticket. Do not rely on a filename alone to identify a certificate. The private key must remain in the approved secrets store and must never be copied into a ticket, chat, or general-purpose workstation directory.

During the approved window, install the renewed certificate using the organization's controlled deployment procedure. Validate the certificate chain and confirm that the gateway presents the expected certificate to a test client. Check both a new connection and an existing session before declaring the change complete. Record the certificate serial number, fingerprint, deployment time, validation result, and change reference in the restricted operations log.

If validation fails, stop the rollout and follow the documented rollback procedure. Do not disable certificate validation to make clients connect. Escalate unexpected chain errors or key mismatches to the certificate service owner.

## Tunnel and gateway diagnostics

Administrators investigating tunnel failures should correlate gateway logs with the reported client timestamp. Search for repeated negotiation failures, rejected authentication, certificate validation errors, and resource exhaustion. A user-reported `VPN-809` may indicate a network-path problem, but it is not sufficient evidence by itself to change gateway policy.

Check whether the issue is isolated to one network, one gateway, or all remote access clients. Compare tunnel establishment rates and active session counts with the normal baseline. Confirm that firewall rules permit only the approved VPN protocols and destination ports. Any temporary rule change requires a ticket, an owner, an expiry time, and a rollback plan.

Do not distribute internal gateway addresses, administrative dashboards, log extracts containing user identifiers, or network diagrams to general users. Provide the helpdesk with only the troubleshooting outcome and the safe next step.

## Change control and recovery

Every production change must have a documented reason, impact assessment, approval, implementation steps, validation checks, and rollback instructions. Store configuration backups in the restricted operations repository. Verify that a backup can be read before making a high-impact change.

After recovery, review the relevant logs and document the root cause, affected service period, and preventive action. Close the change only after the service owner accepts the validation evidence. If the incident suggests credential or key exposure, notify the security team through the approved escalation path rather than treating it as a routine connectivity issue.
