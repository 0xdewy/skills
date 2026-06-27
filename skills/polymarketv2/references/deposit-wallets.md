# Deposit wallets & POLY_1271 (signatureType 3)

Scope: the wallet path for **new API users** — deploy, fund, approve, sync, and
place ERC-1271 orders. Existing Safe/Proxy users are unaffected.
Source: https://docs.polymarket.com/trading/deposit-wallets · last verified: 2026-06-09

## Mental model

A deposit wallet is a per-user **ERC-1967 proxy** deployed by the deposit-wallet
factory; it holds pUSD and conditional tokens on-chain. The owner/session signer
signs **two different, non-interchangeable** payloads:

1. A **DepositWallet `Batch`** for on-chain wallet calls → submitted to the
   relayer as a `WALLET` transaction. Normal 65-byte EIP-712 signature. (See
   `relayer.md`.)
2. A **CLOB order with `signatureType = 3`** → validated by the wallet through
   ERC-1271. Signature is an **ERC-7739-wrapped** `POLY_1271` signature (longer
   than a normal ECDSA sig), **not** the raw order EIP-712 signature.

## Integration flow

1. Pick the owner EOA / session signer.
2. **Deploy** the deposit wallet via relayer `WALLET-CREATE` (no user signature in
   the payload). Poll to `STATE_CONFIRMED` before using it. Address is
   deterministic. (`relayer.md`)
3. **Fund** it: transfer **pUSD to the deposit wallet address**. pUSD on the EOA
   is *not* CLOB buying power.
4. **Approve** trading contracts **from the deposit wallet** — build ERC-20 /
   ERC-1155 approval calldata and submit via a relayer `WALLET` batch. An EOA
   `approve()` does nothing here.
5. **Sync** CLOB balances/allowances with `signature_type = 3` (below).
6. **Trade**: init the CLOB client with the deposit wallet as **funder** and
   `POLY_1271`; order `maker` **and** `signer` must both be the deposit wallet.

## Addresses

Deposit wallet **factory** and **beacon** addresses (Polygon mainnet, chainId
137) are in the canonical registry `references/resources.md` → *Wallet factories*.

## Deterministic address derivation

SDKs do this for you: `deriveDepositWalletAddress()` (TS) /
`get_expected_deposit_wallet()` (Python). Both clone shapes share CREATE2 inputs
and differ only in init-code hash:

```text
walletId = bytes32(owner)            // owner left-padded to 32 bytes
args     = abi.encode(factory, walletId)
salt     = keccak256(args)
uupsWallet   = CREATE2(factory, salt, initCodeHashERC1967(implementation, args))
beaconWallet = CREATE2(factory, salt, initCodeHashERC1967BeaconProxy(beacon, args))
```

Resolve which to use: (1) compute `uupsWallet`; (2) `eth_call` the factory
`BEACON()` (selector `0x49493a4d`) — if it reverts/returns zero, no beacon →
return `uupsWallet`; (3) if non-zero, check `eth_getCode(uupsWallet)` — if it has
bytecode, the user already has a UUPS wallet → return it; (4) else compute and
return `beaconWallet`. New wallets are BeaconProxy clones; legacy UUPS wallets
keep working at their original addresses.

## Sync balance & allowance (after funding / approving)

Use CLOB **L2** auth, with `signature_type = 3`:

```http
GET /balance-allowance/update?asset_type=COLLATERAL&signature_type=3
GET /balance-allowance/update?asset_type=CONDITIONAL&token_id=TOKEN_ID&signature_type=3
```

Rate limits: `GET` balance allowance 200 / 10s · `UPDATE` 50 / 10s.

## Place a raw POLY_1271 order (API users)

`POST /order` with the order using `signatureType: 3`, `maker` and `signer` both
the deposit wallet, and `signature` = the ERC-7739-wrapped sig. The wrapper is a
nested `TypedDataSign` under the **CTF Exchange V2** domain; the nested wallet
fields are `name: "DepositWallet"`, `version: "1"`, `chainId`,
`verifyingContract: <deposit wallet>`, `salt: 0x00…00`. The SDKs build this
wrapper automatically when `POLY_1271` + deposit-wallet funder are configured.

See `troubleshooting.md` for the "invalid signature" / "not enough balance" /
"missing allowance" checklists.
