+++
title = "Remote desktop guide"
classification = "internal"
synthetic = true
+++

# Remote desktop guide

## Who can use remote desktop

Remote desktop is available to approved employees who need to use a managed workstation while away from the office. Access is granted through the normal request process and is tied to an individual account.

Sharing a session, saving another person's credentials, or connecting to an unapproved computer is not permitted.

The demonstration host used in this synthetic guide is rdp.demo.local. It is a training hostname only and does not identify a real production system.

## Starting a session

Connect to the approved network path first, then open the operating system's remote desktop application.

Enter the assigned host name and sign in with your own work account when prompted. Confirm that the displayed computer name matches the instructions before entering credentials.

If the name differs, cancel the connection and ask the helpdesk to verify the assignment.

## Connection failures

If the application cannot find the remote computer, check that the network connection is active and that the host name was entered correctly.

A name-resolution failure may occur before authentication begins. If the sign-in screen appears but rejects the account, report that separately because it indicates a different stage of the connection.

The training error RDP-417 means that the demonstration host refused a new session because its session limit was reached. Wait and try later, or contact support if the issue continues.

Do not repeatedly open new sessions because this can make the limit harder to clear.

## Display and performance

A remote session may feel slow when the local internet connection is unstable or when the remote computer is busy.

Close unused applications inside the remote session and select a display size appropriate for the current network.

Do not lower security settings or disable endpoint protection to improve performance.

## Ending a session

Use Sign out when work is complete and the session should be closed.

Disconnect is appropriate when the session must remain available for a short return, but it leaves the remote session running.

Follow the instructions for the assigned workstation because unattended sessions may be closed automatically.

## Reporting an issue

A support ticket should include the host name, the time of the attempt, the exact error code, and whether the sign-in screen appeared.

Do not attach passwords, authentication codes, or confidential work files.

The helpdesk can use those details to identify whether the issue concerns name resolution, session capacity, or account access.
