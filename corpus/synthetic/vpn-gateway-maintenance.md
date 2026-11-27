+++
title = "VPN gateway maintenance"
classification = "it_restricted"
synthetic = true
+++

# VPN gateway maintenance

## Scope and authorization

This runbook is for the restricted network operations team.

It describes a synthetic maintenance environment and must not be treated as instructions for an actual production gateway.

Only the assigned on-call operator and approved change owner may perform the listed checks.

General employees should use the VPN client troubleshooting guide instead.

## Maintenance target

The training gateway identifier is gw-vpn-07.demo.local.

Its associated change record is CHG-NET-042.

These identifiers are fictional and exist only for the synthetic corpus.

Operators must verify the target against the approved change record before any maintenance action; a similar hostname is not sufficient evidence that the correct system has been selected.

## Pre-change checks

Before the approved window, confirm that the change has an owner, a rollback plan, and a current impact assessment.

Review active sessions and confirm that the support desk has the expected communication.

Record the baseline health state and verify that the standby path is available.

If any prerequisite is missing, pause the change and contact the change owner.

## Certificate validation

The gateway certificate chain must be valid for the expected service identity and within its approved validity period.

A certificate mismatch is a stop condition, not a warning to bypass.

Do not replace trust material from an unverified email or external file.

Record the validation result in the restricted change log.

## Maintenance sequence

During the approved window, follow the change record's sequence and verify each checkpoint before continuing.

The operator should confirm that the standby path remains healthy before moving traffic.

If a checkpoint fails, stop at the documented decision point and use the rollback plan rather than improvising a configuration change.

## Completion and evidence

After the change, verify tunnel establishment, gateway health, and the agreed monitoring signals.

Record timestamps, operator identity, change reference, and observed results in the restricted log.

Do not copy internal topology or gateway configuration into a public ticket.

Escalate unexpected behavior to the network operations lead.
