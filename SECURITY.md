# Security Policy

## Supported Versions

Currently, SVISION is in active production and continuous deployment. Only the latest `main` branch is officially supported for security updates.

| Version | Supported          |
| ------- | ------------------ |
| v1.2.x  | :white_check_mark: |
| v1.1.x  | :white_check_mark: |
| v1.0.x  | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**CRITICAL:** SVISION is deployed on edge industrial hardware managing real-time municipal traffic camera networks. Vulnerabilities in process isolation, Zero-Port IPC bridges, or Unix Domain Socket permissions could expose field hardware or compromise edge telemetry.

**DO NOT** disclose vulnerabilities publicly on GitHub Issues.

If you discover a vulnerability, please report it immediately by emailing:
**security@noxfort.com** *(Noxfort Systems Product Security Team)*.

We will acknowledge receipt of your vulnerability report within 48 hours and strive to send you regular updates about our remediation progress. If a fix is deployed, you will be publicly credited in our release notes (unless you prefer to remain anonymous).
