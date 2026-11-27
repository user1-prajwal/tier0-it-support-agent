+++
title = "VPN client installation"
classification = "internal"
synthetic = true
+++

# VPN client installation

## Before installation
Remote employees use the managed company VPN client to reach internal applications. Confirm that the laptop is enrolled and has completed its normal device updates before starting. The approved package is named Northstar Connect 5.4. Obtain it only from the managed software catalogue. The catalogue checks device eligibility and installs the supported version. Do not use a search-engine download or an installer shared through a chat message.

## Installing the client
Open the software catalogue, search for the approved client, and select Install. Keep the laptop connected to the internet and do not close the installer while it is applying the device profile. When installation completes, restart only if the catalogue requests it. The client should appear in the managed applications list. If the catalogue reports that the device is not eligible, submit a software support request with the device asset tag and the displayed message.

## First connection
Open Northstar Connect and choose the standard employee profile. Sign in with your own work account and complete the normal second-factor prompt. The client establishes an encrypted tunnel after the identity check succeeds. A successful connection is shown by the connected status in the client; opening an internal application is a separate check that confirms the required service is reachable.

## Certificate and sign-in messages
The managed profile supplies the certificate settings automatically. If the client reports that its certificate is missing or untrusted, stop and contact the helpdesk. Do not import a certificate from an email attachment or accept an unfamiliar certificate warning. Include the exact message and the client version in the ticket.

## Common connection errors
A failed connection may be caused by an expired sign-in session, an unavailable internet connection, or a device that has not received its latest management policy. Sign out and sign in once, then check ordinary internet access. If the client displays VPN-826, record that exact code and the time of the attempt. Repeated retries are unlikely to correct a device-policy problem.

## Safe removal and updates
Use the software catalogue to update or remove the client. Do not delete its folders manually because managed settings may remain behind. If a restart or update does not resolve the issue, provide the helpdesk with the client version, operating system version, and exact error code.