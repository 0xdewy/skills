---
title: How to start trading
source_url: https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-start-trading.md
section: onboarding
scrape_status: ok
---
> For the complete documentation index, see [llms.txt](https://hyperliquid.gitbook.io/hyperliquid-docs/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-start-trading.md).

# How to start trading

### What do I need to trade on Hyperliquid?

You can trade on Hyperliquid with a normal defi wallet or by logging in with your email address.

If you choose to use a normal defi wallet, you need: &#x20;

1. An EVM wallet
   * If you don’t already have an EVM wallet (e.g., Rabby, MetaMask, WalletConnect, Coinbase Wallet), you can set one up easily at <https://rabby.io/>.&#x20;
   * After downloading a wallet extension for your browser, create a new wallet.
   * Your wallet has a secret recovery phrase – anyone with access to your private key or seed phrase can access your funds. Do not share these with anyone. Best practice is to record these and store them in a safe physical location.
2. Collateral
   * USDC and ETH (gas to deposit) on Arbitrum, or
   * BTC on Bitcoin, ETH/ENA on Ethereum, SOL/2Z/BONK/FARTCOIN/PUMP/SPX on Solana, MON on Monad, or XPL on Plasma which can be traded for USDC on Hyperliquid

### How do I onboard to Hyperliquid?

There are many different interfaces and apps you can use, including

* [Based](https://based.one/) (web, iOS, Android)
* [Dexari](https://dexari.com/) (iOS, Android)
* [MetaMask](https://metamask.io/) (iOS, Android)
* [Phantom](https://phantom.com/) (web extension, iOS, Android)
* [app.hyperliquid.xyz](https://app.hyperliquid.xyz/trade) (web)

If you choose to log in to app.hyperliquid.xyz with email:&#x20;

1. Click the "Connect" button and enter your email address. After you press "Submit," within a few seconds, a 6 digit code will be sent to your email. Type in the 6 digit code to login.&#x20;
2. Now you're connected. All that's left is to deposit. A new blockchain address is created for your email address. You can send USDC over Arbitrum, BTC on Bitcoin, ETH/ENA on Ethereum, SOL/2Z/BONK/FARTCOIN/PUMP/SPX on Solana, MON on Monad, or XPL on Plasma. It’s easy to do from a centralized exchange or another defi wallet.&#x20;

If you choose to connect to app.hyperliquid.xyz with a defi wallet:&#x20;

1. Click the “Connect” button and choose a wallet to connect. A pop-up will appear in your wallet extension asking you to connect to Hyperliquid. Press “Connect.”
2. Click the “Enable Trading” button. A pop-up will appear in your wallet extension asking you to sign a gas-less transaction. Press "Sign." &#x20;
3. Deposit to Hyperliquid, choosing from USDC on Arbitrum, BTC on Bitcoin, ETH/ENA on Ethereum, SOL/2Z/BONK/FARTCOIN/PUMP/SPX on Solana, MON on Monad, or XPL on Plasma.
   1. For USDC: enter the amount you want to deposit and click “Deposit.” Confirm the transaction in your EVM wallet.&#x20;
   2. For the others: send the spot asset to the destination address shown. Note that you will have to sell this asset for USDC, USDT, or whichever quote asset is used for the assets you're interested in trading.&#x20;
4. You're now ready to trade.

### How do I trade perpetuals on Hyperliquid?

With perpetual contracts, you use USDC as collateral to long or short the token instead of buying the token itself, like in spot trading.&#x20;

1. Using the token selector, choose a token that you want to open a position in.&#x20;
2. Decide if you want to long or short that token. If you expect the token price to go up, you want to long. If you expect the token price to go down, you want to short.
3. Use the slider or type in the size of your position. Position size = your leverage amount \* your collateral&#x20;
4. Lastly, click Place Order. Click Confirm in the modal that appears. You can check the “Don’t show this again” box so you don’t have to confirm each order in the future.&#x20;

### How do I bridge USDC onto Hyperliquid?

1. You will need ETH and USDC on the Arbitrum network, since Hyperliquid’s native bridge is between Hyperliquid and Arbitrum. ETH will only be used as gas for transactions to deposit USDC. Trading on Hyperliquid does not cost gas.
   1. You can use various bridges, such as <https://bridge.arbitrum.io/>, <https://app.debridge.finance/>, <https://swap.mayan.finance/>, <https://app.across.to/bridge?>, <https://routernitro.com/swap>, <https://jumper.exchange/>, <https://synapseprotocol.com/>, and <https://relay.link/bridge>
   2. Alternatively, you can move funds directly to Arbitrum from a centralized exchange, if you’re already using one.
2. Once you have ETH and USDC on Arbitrum, you can deposit by clicking the “Deposit” button on [https://app.hyperliquid.xyz/trade](https://hyperliquid.xyz/trade)

### How do I withdraw USDC from Hyperliquid?

1. On [https://app.hyperliquid.xyz/trade](https://hyperliquid.xyz/trade), click the “Withdraw” button in the bottom right.
2. Enter the amount of USDC you would like to withdraw and click “Withdraw to Arbitrum.” This transaction does not cost gas. There is a $1 withdrawal fee instead.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-start-trading.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
