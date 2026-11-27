+++
title = "Admin console runbook"
classification = "it_restricted"
synthetic = true
+++

# Admin console runbook

## Purpose and access boundary

This document is restricted to the platform administration group.

It describes a fictional training console and does not authorize access to any real system.

Administrators must use an individually assigned privileged identity and the approved secure access path.

Routine employee tasks should be completed through the standard service portal.

## Console identity

The synthetic console is named Aster Admin 3.2 and the training endpoint is admin.demo.local.

The associated control record is ADM-CTRL-22.

These values are invented for this exercise.

Before a privileged session begins, compare the endpoint and task with the approved change or access record.

## Approval requirements

A privileged action requires a documented business reason, an authorized requester, and approval from the designated system owner.

High-impact actions may require a second approver from the platform security function.

An administrator must not approve their own request or rely on an informal chat message as authorization.

## Session handling

Open the console only for the approved task and use the minimum required privilege.

Confirm the target environment before making a change.

Do not leave a privileged session unattended, export credentials, or store session tokens in scripts.

End the session when the approved work is complete.

## Change execution

Follow the approved change plan and record each checkpoint.

If the observed state differs from the expected state, stop and contact the change owner.

Do not make additional changes merely because they appear convenient.

Use the documented rollback decision when a required validation fails.

## Audit evidence

The restricted audit record should identify the operator, approval reference, target, action, start and end times, and outcome.

Include enough detail for an independent reviewer to understand what happened without copying secrets or session tokens.

Store evidence only in the approved restricted location.

## Emergency access

Emergency access is governed by the separate break-glass procedure.

This runbook does not grant permission to use emergency credentials or bypass approval.

If an urgent event requires emergency access, follow the dedicated security process and record the reason and subsequent review.
