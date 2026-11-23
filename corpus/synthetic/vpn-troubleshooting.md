+++
title = "VPN troubleshooting"
classification = "internal"
synthetic = true
+++

# VPN troubleshooting

## Cannot connect

If the VPN client fails to connect, check the following in order before contacting the helpdesk.

First, confirm that your device has a working internet connection by opening a normal website. If the internet is down, the VPN cannot connect. If the website loads but the VPN does not, continue with the next steps.

Second, restart the VPN client. Close it completely and open it again. A stale session can prevent a new tunnel from establishing.

Third, check that you are using the correct gateway address in the client settings. The public gateway address is `vpn.demo.local`. This is the only address you should need to enter as an end user. If the client shows an error code, note it exactly. Error `VPN-809` usually means the client cannot reach the gateway over the current network. Try a different network (for example, a mobile hotspot) to see whether the problem is network-specific. Do not disable the VPN client's certificate validation to work around an error. If the error persists on a different network, contact the helpdesk with the exact error code and the network you tested.

If you see a certificate warning in the client, do not accept it. A certificate warning means the gateway presented a certificate the client does not trust, which can indicate a network interception or a misconfigured gateway. Close the client and report it.

## Slow connection

If the VPN connects but performs poorly, try the following steps.

Disconnect other devices on the same local network that are using heavy bandwidth, such as streaming or large downloads. The VPN speed depends partly on your local internet connection.

Switch the VPN server location to a nearer gateway if your client allows it. A closer gateway usually has lower latency.

Restart the VPN client and reconnect. Long-running sessions can degrade over time.

If slowness persists on more than one gateway and at different times of day, report it to the helpdesk with the approximate time, the gateway you used, and whether the problem affects every application or only some. The helpdesk can correlate the report with gateway health information, but cannot diagnose a network issue from the client side alone.

Do not reinstall the VPN client as a first step for slow performance. Reinstalling can lose your saved gateway settings without fixing a network problem.

## Certificate and gateway questions

The certificate the VPN client validates is issued for the gateway the client connects to. If the client shows a warning about the certificate or the gateway name, treat it as a connectivity or security issue and report it rather than clicking through the warning.

The gateway address (`vpn.demo.local`) is the same for all employees. Do not use a gateway address from an unofficial source, a search result, or a colleague's screenshot. If you are not sure of the correct address, contact the helpdesk.