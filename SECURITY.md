# Security policy

AgentCitadel is pre-release software. The API is not stable and it has not been audited.

## Reporting a vulnerability

Report privately via GitHub's [private vulnerability reporting](https://github.com/emsikes/agentcitadel/security/advisories/new).
Please do not open a public issue for a security report.

Include what you can: affected version or commit, reproduction steps, and the impact you believe it has.

Expect an acknowledgement within a week. Fixes are released as soon as practical, and reporters are
credited in the release notes unless they prefer otherwise.

## Scope

In scope: guard bypasses, policy evaluation flaws that permit a denied tool, approval bypasses,
trace tampering or omission, and anything that causes a fail-open where the design says fail-closed.

Out of scope: vulnerabilities in the models AgentCitadel calls, in tools a user supplies, or in
dependencies — report those upstream.

## Supported versions

Pre-1.0. Only the latest release is supported.