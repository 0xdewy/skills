---
title: Withdrawal has not arrived in my wallet
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawal-has-not-arrived-in-my-wallet.md
section: support
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawal-has-not-arrived-in-my-wallet.md).

# Withdrawal has not arrived in my wallet

### How to check where your withdrawal went <a href="#withdrawal-check" id="withdrawal-check"></a>

{% stepper %}
{% step %}
Check the withdrawal action you conducted

Go to the Portfolio page and check the Deposits & Withdrawals table
{% endstep %}

{% step %}
Check if you used 'Send' or 'Withdraw'

For the withdrawal you are referring to, check if the Action column says “Send Spot,” “Send USDC (Perps Wallet),” or “Withdrawal”&#x20;
{% endstep %}
{% endstepper %}

### **Outcome 1: If you see “Send XXX” instead of “Withdrawal”** <a href="#send-instead-of-withdraw" id="send-instead-of-withdraw"></a>

* You used Send instead of Withdrawal. Send is only to send funds to another account on the Hyperliquid blockchain.
* If you sent funds to an address you control, you can connect the wallet to Hyperliquid and access your funds.
* If you sent it to a CEX, this means that only the CEX address can access the funds you sent. You'll have to wait for the CEX to integrate the Hyperliquid blockchain to coordinate retrieving the funds with them. There is an explicit warning message reminding users not to use Send to withdraw to a CEX.

### **Outcome 2: If you see “Withdrawal”** <a href="#withdrawal-status" id="withdrawal-status"></a>

* If the Status says “Pending,” please wait for the duration estimate stated in the Withdrawal modal. If it takes longer, there is likely congestion on the networks, and the withdrawal will be processed, but take longer than usual.
* If the Status says “Completed,” click the explorer link next to the timestamp to check the destination address that received your withdrawal.
* If the Status says “Failed,” you can try to contact the Unit team which manages BTC, ETH, and SOL deposits and withdrawals via their TG group: <https://t.me/hyperunit>. Note that Unit is an independent team.

### How do I use the Send feature on Hyperliquid and what is it for? <a href="#send-feature" id="send-feature"></a>

* Send is used to send tokens to another account on the Hyperliquid blockchain. It is not to withdraw to another blockchain.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawal-has-not-arrived-in-my-wallet.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
