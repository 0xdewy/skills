# Hyperliquid Docs Local Index

Generated from the official GitBook `llms.txt` index. Load the smallest relevant
reference first, then open individual mirrored pages from `references/docs/` when
the answer depends on exact request schemas, examples, constants, or current wording.

## Sections

### api

- [API](docs/for-developers-api.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api.md)) - Documentation for the Hyperliquid public API
- [Notation](docs/for-developers-api-notation.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/notation.md))
- [Asset IDs](docs/for-developers-api-asset-ids.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/asset-ids.md))
- [Tick and lot size](docs/for-developers-api-tick-and-lot-size.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/tick-and-lot-size.md))
- [Nonces and API wallets](docs/for-developers-api-nonces-and-api-wallets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets.md))
- [Info endpoint](docs/for-developers-api-info-endpoint.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint.md)) - The info endpoint is used to fetch information about the exchange and specific users. The different request bodies result in different corresponding response body schemas.
- [Perpetuals](docs/for-developers-api-info-endpoint-perpetuals.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals.md)) - The section documents the info endpoints that are specific to perpetuals. See Rate limits section for rate limiting logic and weights.
- [Spot](docs/for-developers-api-info-endpoint-spot.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/spot.md)) - The section documents the info endpoints that are specific to spot.
- [Exchange endpoint](docs/for-developers-api-exchange-endpoint.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint.md)) - The exchange endpoint is used to interact with and trade on the Hyperliquid chain. See the Python SDK for code to generate signatures for these requests.
- [Websocket](docs/for-developers-api-websocket.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket.md))
- [Subscriptions](docs/for-developers-api-websocket-subscriptions.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions.md)) - This page describes subscribing to data streams using the WebSocket API.
- [Post requests](docs/for-developers-api-websocket-post-requests.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/post-requests.md)) - This page describes posting requests using the WebSocket API.
- [Timeouts and heartbeats](docs/for-developers-api-websocket-timeouts-and-heartbeats.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/timeouts-and-heartbeats.md)) - This page describes the measures to keep WebSocket connections alive.
- [Error responses](docs/for-developers-api-error-responses.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/error-responses.md))
- [Signing](docs/for-developers-api-signing.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing.md))
- [Rate limits and user limits](docs/for-developers-api-rate-limits-and-user-limits.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits.md))
- [Activation gas fee](docs/for-developers-api-activation-gas-fee.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/activation-gas-fee.md))
- [Priority fees](docs/for-developers-api-priority-fees.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/priority-fees.md)) - Advanced feature for latency-sensitive users
- [Optimizing latency](docs/for-developers-api-optimizing-latency.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/optimizing-latency.md))
- [Bridge2](docs/for-developers-api-bridge2.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/bridge2.md))
- [Deploying HIP-1 and HIP-2 assets](docs/for-developers-api-deploying-hip-1-and-hip-2-assets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/deploying-hip-1-and-hip-2-assets.md))
- [HIP-3 deployer actions](docs/for-developers-api-hip-3-deployer-actions.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/hip-3-deployer-actions.md))
- [HIP-3 deployer actions](docs/for-developers-api-hip-3-deployer-actions-1.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/hip-3-deployer-actions-1.md))

### builder-tools

- [Read Me - Builder Tools](docs/builder-tools-read-me-builder-tools.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/read-me-builder-tools.md))
- [HyperEVM Tools](docs/builder-tools-hyperevm-tools.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/hyperevm-tools.md))
- [HyperCore Tools](docs/builder-tools-hypercore-tools.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/builder-tools/hypercore-tools.md))

### general

- [About Hyperliquid](docs/about-hyperliquid.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/about-hyperliquid.md))
- [Hyperliquid 101 for non-crypto audiences](docs/about-hyperliquid-hyperliquid-101-for-non-crypto-audiences.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/about-hyperliquid/hyperliquid-101-for-non-crypto-audiences.md))
- [Core contributors](docs/about-hyperliquid-core-contributors.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/about-hyperliquid/core-contributors.md))
- [HyperCore](docs/hypercore.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore.md))
- [Referrals](docs/referrals.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/referrals.md))
- [Proposal: Staking referral program](docs/referrals-proposal-staking-referral-program.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/referrals/proposal-staking-referral-program.md))
- [Points](docs/points.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/points.md))
- [Historical data](docs/historical-data.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data.md))
- [Risks](docs/risks.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/risks.md))
- [Bug bounty program](docs/bug-bounty-program.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/bug-bounty-program.md))
- [Audits](docs/audits.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/audits.md))
- [Brand kit](docs/brand-kit.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/brand-kit.md))

### hips

- [Hyperliquid Improvement Proposals (HIPs)](docs/hyperliquid-improvement-proposals-hips.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips.md))
- [HIP-1: Native token standard](docs/hyperliquid-improvement-proposals-hips-hip-1-native-token-standard.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-1-native-token-standard.md))
- [HIP-2: Hyperliquidity](docs/hyperliquid-improvement-proposals-hips-hip-2-hyperliquidity.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-2-hyperliquidity.md))
- [HIP-3: Builder-deployed perpetuals](docs/hyperliquid-improvement-proposals-hips-hip-3-builder-deployed-perpetuals.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-3-builder-deployed-perpetuals.md))
- [HIP-4: Outcome markets](docs/hyperliquid-improvement-proposals-hips-hip-4-outcome-markets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets.md))
- [Frontend checks](docs/hyperliquid-improvement-proposals-hips-frontend-checks.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/frontend-checks.md))

### hypercore

- [Overview](docs/hypercore-overview.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/overview.md))
- [Bridge](docs/hypercore-bridge.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/bridge.md))
- [API servers](docs/hypercore-api-servers.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers.md))
- [Clearinghouse](docs/hypercore-clearinghouse.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/clearinghouse.md))
- [Oracle](docs/hypercore-oracle.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/oracle.md))
- [Order book](docs/hypercore-order-book.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/order-book.md))
- [Staking](docs/hypercore-staking.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/staking.md))
- [Vaults](docs/hypercore-vaults.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults.md))
- [Protocol vaults](docs/hypercore-vaults-protocol-vaults.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/protocol-vaults.md))
- [HyperCore vaults (legacy)](docs/hypercore-vaults-hypercore-vaults-legacy.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/hypercore-vaults-legacy.md))
- [For vault leaders (legacy)](docs/hypercore-vaults-for-vault-leaders-legacy.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/for-vault-leaders-legacy.md))
- [For vault depositors (legacy)](docs/hypercore-vaults-for-vault-depositors-legacy.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/vaults/for-vault-depositors-legacy.md))
- [Multi-sig](docs/hypercore-multi-sig.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/multi-sig.md)) - Advanced Feature
- [Permissionless spot quote assets](docs/hypercore-permissionless-spot-quote-assets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/permissionless-spot-quote-assets.md))
- [Aligned quote assets](docs/hypercore-aligned-quote-assets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/aligned-quote-assets.md))

### hyperevm

- [HyperEVM](docs/hyperevm.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperevm.md))
- [Tools for HyperEVM builders](docs/hyperevm-tools-for-hyperevm-builders.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperevm/tools-for-hyperevm-builders.md))

### hyperevm-dev

- [HyperEVM](docs/for-developers-hyperevm.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm.md))
- [Dual-block architecture](docs/for-developers-hyperevm-dual-block-architecture.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/dual-block-architecture.md))
- [Raw HyperEVM block data](docs/for-developers-hyperevm-raw-hyperevm-block-data.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/raw-hyperevm-block-data.md))
- [Interacting with HyperCore](docs/for-developers-hyperevm-interacting-with-hypercore.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interacting-with-hypercore.md))
- [HyperCore <> HyperEVM transfers](docs/for-developers-hyperevm-hypercore-less-than-greater-than-hyperevm-transfers.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/hypercore-less-than-greater-than-hyperevm-transfers.md))
- [Interaction timings](docs/for-developers-hyperevm-interaction-timings.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/interaction-timings.md))
- [Wrapped HYPE](docs/for-developers-hyperevm-wrapped-hype.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/wrapped-hype.md))
- [JSON-RPC](docs/for-developers-hyperevm-json-rpc.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm/json-rpc.md))

### nodes

- [Nodes](docs/for-developers-nodes.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/nodes.md)) - Documentation for running nodes
- [L1 data schemas](docs/for-developers-nodes-l1-data-schemas.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/nodes/l1-data-schemas.md))
- [Foundation non-validating node](docs/for-developers-nodes-foundation-non-validating-node.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/nodes/foundation-non-validating-node.md))

### onboarding

- [Onboarding](docs/onboarding.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding.md))
- [How to start trading](docs/onboarding-how-to-start-trading.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-start-trading.md))
- [How to use the HyperEVM](docs/onboarding-how-to-use-the-hyperevm.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-use-the-hyperevm.md))
- [How to stake HYPE](docs/onboarding-how-to-stake-hype.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/how-to-stake-hype.md))
- [Connect mobile via QR code](docs/onboarding-connect-mobile-via-qr-code.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/connect-mobile-via-qr-code.md))
- [Export your email wallet](docs/onboarding-export-your-email-wallet.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/export-your-email-wallet.md))
- [Testnet faucet](docs/onboarding-testnet-faucet.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/onboarding/testnet-faucet.md))

### support

- [Read Me - Support Guide](docs/support-read-me-support-guide.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/read-me-support-guide.md)) - This Support Guide is meant to help you resolve common issues that users face on Hyperliquid.
- [Connectivity issues](docs/support-faq-connectivity-issues.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues.md))
- [Connected via wallet](docs/support-faq-connectivity-issues-connected-via-wallet.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-wallet.md)) - Description: I can’t connect my wallet to Hyperliquid / I'm stuck in a loop when trying to sign / My wallet isn’t responding. What should I do?
- [Connected via email](docs/support-faq-connectivity-issues-connected-via-email.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/connectivity-issues/connected-via-email.md)) - Description: I no longer receive verification codes to login with email
- [Deposit or transfer issues (missing / lost)](docs/support-faq-deposit-or-transfer-issues-missing-lost.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost.md)) - Here are the guides in this section:
- [Deposited via Arbitrum network (USDC)](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-arbitrum-network-usdc.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-arbitrum-network-usdc.md)) - Description: You deposited via the Arbitrum network
- [Deposited fiat](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-fiat.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-fiat.md)) - Description: You deposited USDC using fiat, which is managed by Swapped.com
- [Deposited via Bitcoin network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-bitcoin-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-bitcoin-network.md)) - Description: You deposited via the Bitcoin network, which is managed by Unit Protocol.
- [Deposited via Ethereum network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-ethereum-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-ethereum-network.md)) - Description: You deposited via the Ethereum network, which is managed by Unit Protocol.
- [Deposited via Solana network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-solana-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-solana-network.md)) - Description: You deposited via the Solana network, which is managed by Unit Protocol.
- [Deposited via Avalanche network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-avalanche-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-avalanche-network.md)) - Description: You deposited via the Avalanche network, which is managed by Unit Protocol.
- [Deposited via Base network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-base-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-base-network.md)) - Description: You deposited via the Base network, which is managed by Unit Protocol.
- [Deposited via Monad network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-monad-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-monad-network.md)) - Description: You deposited via the Monad network, which is managed by Unit Protocol.
- [Deposited via Plasma network](docs/support-faq-deposit-or-transfer-issues-missing-lost-deposited-via-plasma-network.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/deposited-via-plasma-network.md)) - Description: You deposited via the Plasma network, which is managed by Unit Protocol.
- [Transfer or deposit to USDC (Perps) missing](docs/support-faq-deposit-or-transfer-issues-missing-lost-transfer-or-deposit-to-usdc-perps-missing.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/deposit-or-transfer-issues-missing-lost/transfer-or-deposit-to-usdc-perps-missing.md)) - Description: You transferred USDC from your Spot to Perps balance or deposited USDC via Arbitrum and can’t figure out where it went or why you are not able to use the USDC in your Perps balance.
- [Withdrawal issues](docs/support-faq-withdrawal-issues.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues.md)) - Here are the guides in this section:
- [Withdrawal has not arrived in my wallet](docs/support-faq-withdrawal-issues-withdrawal-has-not-arrived-in-my-wallet.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawal-has-not-arrived-in-my-wallet.md)) - Description: You made a withdrawal, but your funds have not arrived in your wallet or intended destination.
- [My withdrawal keeps getting re-deposited](docs/support-faq-withdrawal-issues-my-withdrawal-keeps-getting-re-deposited.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/my-withdrawal-keeps-getting-re-deposited.md)) - Description: You made a withdrawal, but your funds have been re-deposited.
- [Withdrawing to Phantom Wallet](docs/support-faq-withdrawal-issues-withdrawing-to-phantom-wallet.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/withdrawal-issues/withdrawing-to-phantom-wallet.md)) - Description: You are connected using Phantom Wallet and face issues with withdrawal
- [Trade outcome looks incorrect](docs/support-faq-trade-outcome-looks-incorrect.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect.md)) - Here are the guides in this section:
- [Why was I liquidated?](docs/support-faq-trade-outcome-looks-incorrect-why-was-i-liquidated.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/why-was-i-liquidated.md)) - Description: Your perps position was liquidated and you see "Market Liquidation" in your Trade History
- [How does margining work?](docs/support-faq-trade-outcome-looks-incorrect-how-does-margining-work.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/how-does-margining-work.md)) - Description: You have open cross margin positions and don’t understand how margin is attributed to positions
- [My TP/SL did not execute correctly](docs/support-faq-trade-outcome-looks-incorrect-my-tp-sl-did-not-execute-correctly.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/my-tp-sl-did-not-execute-correctly.md)) - Description: You set a TP/SL and believe it was not executed correctly
- [I can't sell leftover spot assets](docs/support-faq-trade-outcome-looks-incorrect-i-cant-sell-leftover-spot-assets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/i-cant-sell-leftover-spot-assets.md)) - Description:  I have a small amount of a spot asset that I can’t sell
- [What does "Action already expired" mean?](docs/support-faq-trade-outcome-looks-incorrect-what-does-action-already-expired-mean.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/trade-outcome-looks-incorrect/what-does-action-already-expired-mean.md)) - Description: You received an error message saying '"Action already expired"' when placing an order
- [HyperEVM issues](docs/support-faq-hyperevm-issues.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues.md)) - Here are the guides in this section:
- [Accidentally transferred to HyperEVM](docs/support-faq-hyperevm-issues-accidentally-transferred-to-hyperevm.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/accidentally-transferred-to-hyperevm.md)) - Description: You clicked the “Transfer to/from EVM” button and can’t figure out what happened
- [Can’t see my HyperEVM assets in wallet extension](docs/support-faq-hyperevm-issues-cant-see-my-hyperevm-assets-in-wallet-extension.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/cant-see-my-hyperevm-assets-in-wallet-extension.md)) - Description: You are using the EVM and don’t see your assets on the EVM in your wallet extension
- [Gas problem on EVM](docs/support-faq-hyperevm-issues-gas-problem-on-evm.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/hyperevm-issues/gas-problem-on-evm.md)) - Description: You are having issues paying for gas or getting transactions through on the HyperEVM
- [Portfolio margin](docs/support-faq-portfolio-margin.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/portfolio-margin.md))
- [Unstaking & link staking issues](docs/support-faq-unstaking-and-link-staking-issues.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/unstaking-and-link-staking-issues.md)) - Here are the guides in this section:
- [Unstaking transfer taking more than 7 days](docs/support-faq-unstaking-and-link-staking-issues-unstaking-transfer-taking-more-than-7-days.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/unstaking-and-link-staking-issues/unstaking-transfer-taking-more-than-7-days.md)) - Description: You believe that you unstaked HYPE and the transfer has taken >7 days. Your unstaked HYPE has not reached your Spot balance
- [Staking and trading account linking issues](docs/support-faq-unstaking-and-link-staking-issues-staking-and-trading-account-linking-issues.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/unstaking-and-link-staking-issues/staking-and-trading-account-linking-issues.md)) - Description: You have questions after linking a staking and trading account
- [Building on Hyperliquid](docs/support-faq-building-on-hyperliquid.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/building-on-hyperliquid.md)) - Here are the guides in this section:
- [I have API related questions](docs/support-faq-building-on-hyperliquid-i-have-api-related-questions.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/building-on-hyperliquid/i-have-api-related-questions.md)) - Description: You are building on HyperCore or HyperEVM
- [I want to deploy a spot token or list a perp](docs/support-faq-building-on-hyperliquid-i-want-to-deploy-a-spot-token-or-list-a-perp.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/building-on-hyperliquid/i-want-to-deploy-a-spot-token-or-list-a-perp.md))
- [I got scammed/hacked](docs/support-faq-i-got-scammed-hacked.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/support/faq/i-got-scammed-hacked.md)) - Description: Your account was compromised / you see transactions you did not authorize / your funds are missing.

### trading

- [Trading](docs/trading.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading.md))
- [Fees](docs/trading-fees.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees.md))
- [Sub-accounts](docs/trading-sub-accounts.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/sub-accounts.md))
- [Builder codes](docs/trading-builder-codes.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/builder-codes.md))
- [Perpetual assets](docs/trading-perpetual-assets.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/perpetual-assets.md))
- [Contract specifications](docs/trading-contract-specifications.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications.md))
- [Margining](docs/trading-margining.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margining.md))
- [Account abstraction modes](docs/trading-account-abstraction-modes.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/account-abstraction-modes.md))
- [Portfolio margin](docs/trading-portfolio-margin.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-margin.md)) - Alpha mode
- [Margin tiers](docs/trading-margin-tiers.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margin-tiers.md))
- [Robust price indices](docs/trading-robust-price-indices.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/robust-price-indices.md))
- [Liquidations](docs/trading-liquidations.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/liquidations.md))
- [Auto-deleveraging](docs/trading-auto-deleveraging.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/auto-deleveraging.md))
- [Funding](docs/trading-funding.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/funding.md))
- [Order book](docs/trading-order-book.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-book.md))
- [Order types](docs/trading-order-types.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/order-types.md))
- [Take profit and stop loss orders (TP/SL)](docs/trading-take-profit-and-stop-loss-orders-tp-sl.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/take-profit-and-stop-loss-orders-tp-sl.md))
- [Entry price and pnl](docs/trading-entry-price-and-pnl.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/entry-price-and-pnl.md))
- [Self-trade prevention](docs/trading-self-trade-prevention.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/self-trade-prevention.md))
- [Index perpetual contracts](docs/trading-index-perpetual-contracts.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/index-perpetual-contracts.md))
- [Uniswap perpetuals](docs/trading-uniswap-perpetuals.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/uniswap-perpetuals.md))
- [Hyperps](docs/trading-hyperps.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/hyperps.md))
- [Delisting](docs/trading-delisting.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/delisting.md))
- [Market making](docs/trading-market-making.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/market-making.md))
- [Portfolio graphs](docs/trading-portfolio-graphs.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-graphs.md))
- [Miscellaneous UI](docs/trading-miscellaneous-ui.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/miscellaneous-ui.md))

### validators

- [Validators](docs/validators.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/validators.md))
- [Running a validator](docs/validators-running-a-validator.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/validators/running-a-validator.md))
- [Delegation program](docs/validators-delegation-program.md) ([source](https://hyperliquid.gitbook.io/hyperliquid-docs/validators/delegation-program.md))
