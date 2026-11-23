+++
title = "Disk encryption recovery"
classification = "it_restricted"
synthetic = true
+++

# Disk encryption recovery

## Confirm the recovery request

This procedure is for authorized IT support personnel handling a managed device that cannot unlock its encrypted system drive. Disk encryption protects data if a device is lost or accessed outside approved controls. A recovery request must be associated with a verified employee, an assigned asset, and an approved support ticket before any recovery information is retrieved.

Confirm the device asset tag, assigned user, device serial number, and the reason the recovery screen appeared. Compare those details with the device-management inventory. A recovery key must never be issued solely because a caller knows an employee name or asset tag. Complete the required identity and device ownership checks using the approved support workflow.

The recovery record is stored in the restricted device-management service. Authorized technicians retrieve it using the approved utility `KeyVaultCLI` from a managed support workstation. The utility requires the technician's individual access and records the request reference. Do not copy recovery keys into email, chat, screenshots, or general ticket comments. Reveal the key only through the approved protected support procedure and only to the verified user associated with the device.

## Retrieve and validate a recovery key

Before retrieving a key, confirm that the ticket has the required approval and that the device identifier matches the inventory record exactly. Use `KeyVaultCLI` to query the managed record by the approved device identifier. Review the returned asset association and key status before proceeding. If the utility reports multiple records or an identifier mismatch, stop and ask the device-management owner to resolve the inventory discrepancy.

Provide the recovery information only through the approved secure channel. Ask the user to enter it directly into the device recovery screen. Do not ask the user to read the complete key aloud or send a photograph of the screen. Once the device unlocks, confirm that it starts normally and that its management status is healthy.

The recovery key is not a replacement for the user's normal account password. Do not disable encryption or remove device protection as a shortcut. If the key is rejected, verify that the correct recovery record was selected and escalate through the device-management team.

## Lost device and suspected exposure

If a device is reported lost, follow the lost-device process and notify the responsible security contact. Do not retrieve or disclose a recovery key for a device whose ownership or status is unclear. If a key may have been exposed, record the incident in the restricted ticket, notify the device-security owner, and follow the approved key rotation or device remediation process.

After the request is complete, record the ticket reference, technician identity, device identifier, retrieval outcome, and validation result. The ticket must not contain the recovery key itself. Review access logs if the request was unusual or if the user reports unexpected recovery prompts.
