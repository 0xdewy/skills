---
title: I got scammed/hacked
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/i-got-scammed-hacked.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/i-got-scammed-hacked.md).

# I got scammed/hacked

If you notice unauthorized transactions, missing funds, or an unknown multi-sig on your Hyperliquid account, your wallet was likely compromised.&#x20;

Hyperliquid is non-custodial. Only someone with access to your private key or seed phrase can sign transactions on your address’ behalf. If you see activity you didn’t initiate, it’s highly likely that your key was compromised, meaning someone else has control of your address.

### What to do

* Stop using the compromised address. Treat it as permanently unsafe ("burned")
* Create a new wallet address using a trusted wallet provider&#x20;
* Transfer any remaining funds from your old wallet to your new one—this applies across all apps, not just Hyperliquid
* Send any assets you may have on the HyperEVM to your new address (This is also applicable if your HyperCore address has been converted into a multi-sig you do not control)
* Revoke smart contract permissions via <https://revoke.cash> to limit further access to your wallet
* Clear your browser's cache and cookies, especially if you suspect there may be malware or phishing
* Identify how you were compromised and determine if your device has malware. This helps ensure you do not repeat the same mistakes again

### Best practices moving forward

Being in DeFi means being responsible about self-custody and keeping your own assets safe. Remember to always be vigilant

* Never share your seed phrase and private key (Never input it into a website and never share it with a 'support' person)
* Consider using a hardware wallet for a more secure setup (e.g., Ledger, Trezor, Keystone). Hardware wallets can be paired with browser wallets like Rabby to keep your private key off the browser
* Never rush to perform actions. Always read and double-check any transaction you sign (Review warnings or alerts from your wallet, if there is insufficient information, do not sign)
* Never click on unknown links, and beware of sponsored links on your search engine, always verify (Cross reference links against official Twitter accounts, DefiLlama, CoinGecko etc.). Bookmark frequently visited sites to avoid phishing attempts
* Never download unknown or unverified applications
* Never download PDFs from unknown users or sources
* Assume most DMs are scams. Be suspicious if someone asks you to install software or sends a link out of context
* Keep your browsers and extensions up to date; delete any extensions that are no longer maintained


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/i-got-scammed-hacked.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
