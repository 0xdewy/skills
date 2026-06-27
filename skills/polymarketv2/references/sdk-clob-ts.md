# Standalone TypeScript CLOB + relayer client

Scope: the standalone v2 clients (alternative to the unified SDK). Use
`@polymarket/clob-client-v2` for orders/data and
`@polymarket/builder-relayer-client` for deposit-wallet deploy + wallet batches.
Source: https://github.com/Polymarket/clob-client-v2 · https://github.com/Polymarket/builder-relayer-client · last verified: 2026-06-09

## Install

```bash
npm install @polymarket/clob-client-v2@latest \
  @polymarket/builder-relayer-client @polymarket/builder-signing-sdk viem
```

## Auth / create creds

```ts
import { ClobClient } from "@polymarket/clob-client-v2";
import { createWalletClient, http } from "viem";
import { privateKeyToAccount } from "viem/accounts";

const account = privateKeyToAccount(process.env.PRIVATE_KEY as `0x${string}`);
const signer  = createWalletClient({ account, transport: http() });
const client  = new ClobClient({ host: "https://clob.polymarket.com", chain: 137, signer });
const creds   = await client.createOrDeriveApiKey();
```

## Deploy + fund + approve (relayer)

```ts
import { BuilderApiKeyCreds, BuilderConfig } from "@polymarket/builder-signing-sdk";
import { RelayClient } from "@polymarket/builder-relayer-client";
import type { DepositWalletCall } from "@polymarket/builder-relayer-client";

const builderConfig = new BuilderConfig({ localBuilderCreds: {
  key: process.env.BUILDER_API_KEY!, secret: process.env.BUILDER_SECRET!,
  passphrase: process.env.BUILDER_PASS_PHRASE! } as BuilderApiKeyCreds });

const relayer = new RelayClient(process.env.RELAYER_URL!, 137, walletClient, builderConfig);
const depositWallet = await relayer.deriveDepositWalletAddress();
await (await relayer.deployDepositWallet()).wait();           // WALLET-CREATE

const calls: DepositWalletCall[] = [{ target: process.env.PUSD_ADDRESS!, value: "0", data: approveCalldata }];
const deadline = Math.floor(Date.now()/1000 + 600).toString();
await (await relayer.executeDepositWalletBatch(calls, depositWallet, deadline)).wait();   // WALLET batch
```

`deployDepositWallet()` adds no user signature; `executeDepositWalletBatch()`
fetches the `WALLET` nonce and signs the `Batch` under domain
`{ name: "DepositWallet", version: "1", chainId, verifyingContract: depositWallet }`.

## Trade from the deposit wallet (POLY_1271)

```ts
import { AssetType, ClobClient, OrderType, Side, SignatureTypeV2 } from "@polymarket/clob-client-v2";

const clob = new ClobClient({
  host: process.env.CLOB_API_URL!, chain: 137, signer: walletClient, creds,
  signatureType: SignatureTypeV2.POLY_1271,    // = 3
  funderAddress: depositWallet,
});
await clob.updateBalanceAllowance({ asset_type: AssetType.COLLATERAL });
const order = await clob.createAndPostOrder(
  { tokenID: process.env.TOKEN_ID!, price: 0.5, size: 10, side: Side.BUY },
  { tickSize: "0.01", negRisk: false },
  OrderType.GTC,
);
```

Get `tickSize` / `negRisk` from `GET /book` (`api-clob-public.md`). For existing
Safe/Proxy wallets, set the matching `signatureType` (0/1/2) and that funder
instead. See `troubleshooting.md` if an order is rejected.
