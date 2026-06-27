---
title: Bug bounty program
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/bug-bounty-program.md
section: general
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/bug-bounty-program.md).

# Bug bounty program

### In scope

* On mainnet, any bug that would cause an outage or logical error on nodes or API servers is in scope.&#x20;
* Experimental features on testnet are not in scope, unless otherwise announced in [Discord](https://discord.gg/hyperliquid) or Telegram announcements, though bug reports are still appreciated for these features.

### Submission process

* Write a report regarding the bug and include detailed reproduction steps and a proof of concept to validate your findings. Submit your report to <bugbounty@hyperfoundation.org>.
* If the same bug is reported by multiple individuals or entities, the first report will be honored.&#x20;
* Rewards will be paid in USDC on Hyperliquid for responsible disclosure of bugs based on their severity.&#x20;
* We agree not to pursue legal action in respect of any research conducted in good faith and in compliance with this program.&#x20;
* The time and energy that go into all bug reports is deeply appreciated.

### Prohibited activity&#x20;

* Testing on mainnet code; all testing should be done on testnet or local forks.
* Phishing or other social engineering attacks.
* Extended, large scale DDOS attacks. Attacks involving mishandling of temporary spikes in load are allowed.
* Testing with third-party systems and applications (e.g. browser extensions) as well as websites (e.g. SSO providers, advertising networks).
* Submitting ransom demands or threats.
* Publicly disclosing a bug report before it has been fixed and paid.
* Threatening to publish or publishing anyone’s personally identifiable information or other sensitive information without their consent.
* Exploiting vulnerabilities for personal financial gain beyond the rewards described in this program.
* Attempting to bypass these procedures or engaging in unauthorized activities outside the outlined scope.

### Eligibility

* You must submit your report to <bugbounty@hyperfoundation.org>. Do not use external sites.&#x20;
* You must comply with the KYC/KYB policy and procedures.&#x20;
* You must be able to receive USDC on Hyperliquid.&#x20;
* You must maintain confidentiality regarding vulnerabilities and communications until authorized for disclosure by us.
* We must be able to reproduce your findings. All bounty submissions will be paid out based on their classification. Classification examples are subject to change. &#x20;
* Contributors to the development of the code being tested are not eligible to participate in the program in relation to such code.

### Ineligibility

* Reports lacking sufficient detail, including step-by-step instructions, reproducible examples, or proof of concept.
* Vulnerabilities that require highly unlikely or unreasonable user behavior to exploit.
* Vulnerabilities caused by outdated software, unpatched browsers, or systems no longer supported by Hyperliquid.
* Vulnerabilities that rely on root access, jailbreaking, or other modifications to user devices.
* Issues within third-party libraries, extensions, tools, or applications that do not lead to a direct Hyperliquid vulnerability.
* Bugs or errors unrelated to security, such as minor performance issues.
* Bugs or errors contingent on extreme or unrealistic market conditions that do not reflect real-world scenarios.

### General conditions

* Payment will not be made for submissions that do not meet the program’s requirements or that are excluded under the program’s scope or ineligibility criteria.&#x20;
* We reserve the right to determine the validity and classification of any submission at our sole discretion.
* All submissions become the property of the Hyper Foundation. We reserve the right to use, modify, or disclose submissions for security purposes without requiring additional consent.

### Classification examples

* Critical (<1M USDC): Significant loss of user funds. Violation of L1 execution invariants.
* High (<50k USDC): Network downtime that does not lead to incorrect state.
* Medium (<10k USDC): API server performance issues.&#x20;

For the avoidance of doubt, rewards are determined based on the severity of the issue reported, and payouts may vary within the ranges listed above. Severity is determined based on both impact and likelihood of occurrence.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/bug-bounty-program.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
