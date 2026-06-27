# Security Policy

Rectury connects language models to tools that can interact with a user's
computer. Security reports are taken seriously, especially when they involve
unexpected tool execution, access to files, exposed credentials, or actions
performed without user approval.

## Supported Versions

Rectury is currently in alpha and does not have stable versioned releases yet.

| Version | Supported |
| --- | --- |
| Latest `main` branch | Yes |
| Older commits | No |
| Forks and modified versions | No |

Security fixes are applied to the latest version of the `main` branch.

## Reporting a Vulnerability

> [!IMPORTANT]
> Do not report security vulnerabilities in a public issue.

Use GitHub's private vulnerability reporting page:

[Report a vulnerability privately](https://github.com/Rectury-AI/Rectury-Desktop/security/advisories/new)

If private vulnerability reporting is not available, contact a repository
maintainer privately before publishing technical details.

Include as much of the following information as possible:

- [ ] A clear description of the vulnerability.
- [ ] Steps needed to reproduce it.
- [ ] The affected operating system and Python version.
- [ ] The affected commit or Rectury version.
- [ ] The possible impact.
- [ ] Logs, screenshots, or proof-of-concept code when useful.
- [ ] Any suggested fix or mitigation.

Remove API keys, tokens, personal files, conversation data, and other secrets
from the report.

## What to Expect

Maintainers will review the report and may ask for more information. If the
issue is confirmed, work will begin on a fix and a coordinated disclosure.

Please allow maintainers time to investigate before sharing the vulnerability
publicly. Rectury does not currently operate a bug bounty program.

## Security Scope

Examples of relevant security issues include:

- Tools running without the required user approval.
- Commands or file operations escaping their intended boundaries.
- API keys or other credentials being exposed.
- Conversation data being read or written by an unauthorized process.
- Prompt or tool input causing unintended local actions.
- Unsafe handling of paths, arguments, or tool results.
- Dependency vulnerabilities that directly affect Rectury.

General bugs, feature requests, and usability problems should be reported in
the [public issue tracker](https://github.com/Rectury-AI/Rectury-Desktop/issues).

## Safe Usage

Rectury is experimental software. Run it only in projects and directories you
trust. Review tool behavior before enabling sensitive actions, and never place
API keys directly in source code or committed files.
