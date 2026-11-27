+++
title = "Account lockout policy"
classification = "internal"
synthetic = true
+++

# Account lockout policy

## Failed sign-in threshold

The synthetic employee account policy allows six consecutive invalid password attempts before an account is temporarily locked.

The counter applies to interactive sign-in attempts against the managed identity service. A successful sign-in resets the consecutive-failure counter.

The threshold is different from the password-reset verification limit, which is described in the password reset guide.

## Lockout duration

A standard lockout lasts 20 minutes from the time the threshold is reached.

The account becomes eligible for sign-in again after that interval, provided no additional failed attempts extend the lockout.

Employees should wait for the full period rather than repeatedly testing possible passwords.

## What employees should do

If the account is locked, stop attempting to sign in and check whether the password was recently changed.

Update saved credentials only in approved applications and managed devices.

If access is still unavailable after the stated period, contact the helpdesk and provide the time of the first lockout message.

Never send a password to support.

## Service accounts and exceptions

This employee policy does not define the controls for service identities, automated jobs, or privileged administrator accounts.

Those identities follow separate ownership and security procedures.

Employees must not use a service account to bypass an employee lockout or ask a colleague to sign in on their behalf.

## Helpdesk verification

Support staff verify the requester's identity using the approved recovery process before assisting with an account lockout.

They may confirm whether a lockout is active and explain the next permitted step.

They must not disclose another user's account status or reset credentials based only on a message from an unverified sender.

## Distinguishing lockout from password reset

A lockout is a temporary restriction caused by repeated unsuccessful sign-in attempts.

A password reset is a controlled process for replacing a forgotten or compromised password after identity verification.

Resetting a password does not remove the need to complete identity checks, and waiting for a lockout to expire does not change the password.
