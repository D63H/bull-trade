# Security

Bull Desk handles brokerage credentials. The rules that keep them safe:

- The App Key and App Secret enter the desk only through the agent platform's secure secret store, never through chat, never written under `/workspace`.
- The Webull Trading API used by this desk has no withdrawal, transfer or ACH endpoints. The desk never requests Broker API access, which is where money movement lives.
- All of a user's Bots share one computer. Bot names are not a security boundary; assume anything on the computer is readable by every Bot. That is why only trade-scoped credentials are ever provisioned, and why the sandbox comes first.
- Sandbox (`uat`) and production (`prod`) credentials are separate keys. Keep them in separate secrets and never let a `prod` value into a session whose ticket says paper.
- Rotation: Webull's portal invalidates the old key the moment a new one is generated. Rotate immediately on any suspicion; playbook G in `skills/desk-incident-response/SKILL.md`.
- Report problems with this repository's instructions by opening an issue. Report Webull platform vulnerabilities to Webull, not here.
