# Security policy

Report vulnerabilities through GitHub private vulnerability reporting when available.

Security-sensitive areas include:

- path handling and starter-file writes;
- manifest and event verification;
- objective or constraint tampering;
- release workflow permissions;
- unsafe archive or artifact handling;
- public examples that accidentally contain real operational data.

This project does not execute external solvers, shell strings, or network calls in its reference runtime.
