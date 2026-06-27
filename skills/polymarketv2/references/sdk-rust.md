# Rust CLOB client

Scope: the Rust v2 CLOB client. It supports the CLOB order path (including
deposit-wallet / POLY_1271) but has **no relayer client** — deploy wallets and
submit `WALLET` batches via the TS/Python relayer client or the raw API
(`relayer.md`), then trade with this client.
Source: https://github.com/Polymarket/rs-clob-client-v2 · https://crates.io/crates/polymarket_client_sdk_v2 · last verified: 2026-06-09

## Install

```bash
cargo add polymarket_client_sdk_v2 --features clob
```

## Auth / create creds

```rust
use std::str::FromStr;
use polymarket_client_sdk_v2::POLYGON;
use polymarket_client_sdk_v2::auth::{LocalSigner, Signer};
use polymarket_client_sdk_v2::clob::{Client, Config};

let signer = LocalSigner::from_str(&std::env::var("POLYMARKET_PRIVATE_KEY")?)?
    .with_chain_id(Some(POLYGON));
let client = Client::new("https://clob.polymarket.com", Config::default())?
    .authentication_builder(&signer)
    .authenticate()           // creates or derives creds, then builds the client
    .await?;
let creds = client.credentials();
```

## Trade from the deposit wallet (POLY_1271)

```rust
use std::str::FromStr as _;
use polymarket_client_sdk_v2::auth::{LocalSigner, Signer as _};
use polymarket_client_sdk_v2::clob::types::request::UpdateBalanceAllowanceRequest;
use polymarket_client_sdk_v2::clob::types::{AssetType, OrderType, Side, SignatureType};
use polymarket_client_sdk_v2::clob::{Client, Config};
use polymarket_client_sdk_v2::types::{Address, Decimal, U256};
use polymarket_client_sdk_v2::{POLYGON, PRIVATE_KEY_VAR};

let token_id = U256::from_str(&std::env::var("TOKEN_ID")?)?;
let deposit_wallet = Address::from_str(&std::env::var("DEPOSIT_WALLET")?)?;
let signer = LocalSigner::from_str(&std::env::var(PRIVATE_KEY_VAR)?)?.with_chain_id(Some(POLYGON));

let client = Client::new(&std::env::var("CLOB_API_URL")?, Config::default())?
    .authentication_builder(&signer)
    .funder(deposit_wallet)
    .signature_type(SignatureType::Poly1271)        // = 3
    .authenticate()
    .await?;

client.update_balance_allowance(
    UpdateBalanceAllowanceRequest::builder().asset_type(AssetType::Collateral).build()
).await?;

let _resp = client.limit_order()
    .token_id(token_id).side(Side::Buy)
    .price(Decimal::from_str("0.50")?).size(Decimal::from_str("10")?)
    .order_type(OrderType::GTC)
    .build_sign_and_post(&signer)
    .await?;
```

Setting `SignatureType::Poly1271` + a deposit-wallet `funder` makes the client
emit `signatureType = 3` and build the wrapped ERC-1271 order signature. Geoblock
helper: `client.check_geoblock().await?` (`.blocked`, `.country`).
