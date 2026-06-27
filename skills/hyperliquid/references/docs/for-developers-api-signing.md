---
title: Signing
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing.md
section: api
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing.md).

# Signing

It is recommended to use an existing SDK instead of manually generating signatures. There are many potential ways in which signatures can be wrong. An incorrect signature results in recovering a different signer based on the signature and payload and results in one of the following errors:\
`"L1 error: User or API Wallet 0x0123... does not exist."`\
`Must deposit before performing actions. User: 0x123...`\
where the returned address does not match the public address of the wallet you are signing with. The returned address also changes for different inputs.\
An incorrect signature does not indicate why it is incorrect which makes debugging more challenging. To debug this it is recommended to read through the Python SDK carefully and make sure the implementation matches exactly. If that doesn't work, add logging to find where the output diverges.

Some common errors:\
1\. Not realizing that there are two signing schemes (the Python SDK methods are `sign_l1_action` vs `sign_user_signed_action`).\
2\. Not realizing that the order of fields matter for msgpack.\
3\. Issues with trailing zeroes on numbers.\
4\. Issues with upper case characters in address fields. It is recommended to lowercase any address before signing and sending. Sometimes the field is parsed as bytes, causing it to be lowercased automatically across the network.\
5\. Believing that the signature must be correct because calling recover signer locally results in the correct address. The payload for recover signer is constructed based on the action and does not necessarily match.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
