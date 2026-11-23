+++
title = "Incident severity runbook"
classification = "security_restricted"
synthetic = true
+++

# Incident severity runbook

## Severity levels

This runbook is for the security response team and contains internal incident classification guidance. A security incident is an event that may affect the confidentiality, integrity, or availability of organizational information or services. The responder who receives the initial report should preserve the original report, record the time received, and route it to the designated incident lead.

Severity 1 is used for a confirmed or highly credible event with broad or critical impact, such as active compromise of a privileged account, widespread exposure of sensitive records, or disruption of a critical service with no safe workaround. Severity 1 requires immediate notification of the incident lead and the on-call security manager. The response team should coordinate containment while preserving evidence.

Severity 2 applies to a credible security event with limited but material impact, such as suspected compromise of one employee account with access to internal systems, or confirmed malware on a managed endpoint that has not spread. Notify the incident lead promptly and begin the approved investigation and containment steps.

Severity 3 applies to a lower-impact event requiring investigation but with no current evidence of material compromise. Examples include a blocked phishing attempt reported by an employee or a suspicious attachment that was not opened. Record the evidence and assign an owner for follow-up. Reclassify the incident if new facts change the impact assessment.

## Initial triage and evidence handling

Collect the reporter's contact details, affected account or asset, approximate event time, observed behavior, and any relevant ticket or alert identifier. Do not ask the reporter to forward suspicious attachments to an ordinary mailbox. Use the approved evidence collection process and preserve original timestamps and metadata where possible.

Do not delete files, wipe devices, or reset accounts before the incident lead has considered evidence preservation and containment needs. If immediate containment is necessary to prevent ongoing harm, follow the emergency procedure and document who authorized the action, what changed, and when it occurred.

Treat logs, screenshots, message headers, and endpoint records as potentially sensitive. Store them only in the restricted incident workspace. Limit access to responders with an operational need. Do not paste credentials, session tokens, or private keys into incident notes.

## Escalation and closure

Escalate immediately when there is evidence of privileged access, regulated or confidential data exposure, multiple affected users, active attacker activity, or uncertainty about a critical service. The incident lead decides whether legal, privacy, communications, or service-owner teams must be engaged.

An incident may be closed only after containment is confirmed, required evidence is retained, affected owners are notified, and follow-up actions have assigned owners and due dates. The closure summary should describe impact, timeline, root cause where known, containment, recovery, and lessons learned without reproducing secrets or unnecessary personal information.
