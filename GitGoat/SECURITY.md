# Security Policy

## Supported Versions

Only the `main` branch is supported. There are no versioned releases with
security backports.

## Reporting a Vulnerability

Report vulnerabilities privately through
[GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
for this repository. Do not open public issues for security reports.

## Credentials in this repository — no reuse

GitGoat is a deliberately vulnerable test tool. The repository intentionally
contains dummy credentials (member tokens in `config.yaml` and encoded
secrets under `secrets/`) so that secret scanners and misconfiguration
detectors can be tested against it.

- These credentials are invalid dummy values for disposable accounts. Do not
  reuse them anywhere, and do not replace them with real credentials.
- Never commit a real personal access token to this repository. The
  `github_token` used to run GitGoat must only be supplied at run time as an
  environment variable and must never be passed as a Docker build argument.
- Tokens that fail authentication (expired, revoked, or invalid) are locked
  out by the API client for the remainder of the run and will not be reused.
- Keep the organizations and repositories created by GitGoat private so that
  the generated test secrets are not exposed publicly.
