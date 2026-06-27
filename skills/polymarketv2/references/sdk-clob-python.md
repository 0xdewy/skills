# Standalone Python CLOB + relayer client

Scope: the standalone v2 clients (alternative to the unified SDK). Use
`py-clob-client-v2` for orders/data and `py-builder-relayer-client` for
deposit-wallet deploy + wallet batches.
Source: https://github.com/Polymarket/py-clob-client-v2 · https://github.com/Polymarket/py-builder-relayer-client · last verified: 2026-06-09

> The current packages are **`py-clob-client-v2`** and
> **`py-builder-relayer-client`** — not the legacy `py-clob-client`. See
> `v1-v2-migration.md`.

## Install

```bash
pip install py-clob-client-v2 py-builder-relayer-client
```

## Auth / create creds

```python
from py_clob_client_v2 import ClobClient
import os
client = ClobClient(host="https://clob.polymarket.com", chain_id=137, key=os.getenv("PRIVATE_KEY"))
creds = client.create_or_derive_api_key()      # {"apiKey","secret","passphrase"}
```

## Deploy + fund + approve (relayer)

```python
import os, time
from py_builder_relayer_client.client import RelayClient
from py_builder_relayer_client.models import DepositWalletCall, TransactionType
from py_builder_signing_sdk.config import BuilderApiKeyCreds, BuilderConfig

builder_config = BuilderConfig(local_builder_creds=BuilderApiKeyCreds(
    key=os.environ["BUILDER_API_KEY"], secret=os.environ["BUILDER_SECRET"],
    passphrase=os.environ["BUILDER_PASS_PHRASE"]))

relayer = RelayClient(os.environ["RELAYER_URL"], 137, os.environ["PRIVATE_KEY"], builder_config)
deposit_wallet = relayer.get_expected_deposit_wallet()
relayer.deploy_deposit_wallet().wait()                                   # WALLET-CREATE

nonce = str(relayer.get_nonce(relayer.signer.address(), TransactionType.WALLET.value)["nonce"])
call  = DepositWalletCall(target=os.environ["PUSD_ADDRESS"], value="0", data=approve_calldata)
relayer.execute_deposit_wallet_batch(
    calls=[call], wallet_address=deposit_wallet, nonce=nonce,
    deadline=str(int(time.time()) + 600)).wait()                          # WALLET batch
```

## Trade from the deposit wallet (POLY_1271)

```python
import os
from py_clob_client_v2 import (
    ApiCreds, AssetType, BalanceAllowanceParams, ClobClient,
    OrderArgs, OrderType, PartialCreateOrderOptions, Side, SignatureTypeV2,
)

creds = ApiCreds(api_key=os.environ["CLOB_API_KEY"], api_secret=os.environ["CLOB_SECRET"],
                 api_passphrase=os.environ["CLOB_PASS_PHRASE"])
clob = ClobClient(host=os.environ["CLOB_API_URL"], chain_id=137, key=os.environ["PRIVATE_KEY"],
                  creds=creds, signature_type=SignatureTypeV2.POLY_1271,   # = 3
                  funder=deposit_wallet)

clob.update_balance_allowance(BalanceAllowanceParams(
    asset_type=AssetType.COLLATERAL, signature_type=SignatureTypeV2.POLY_1271))

resp = clob.create_and_post_order(
    order_args=OrderArgs(token_id=os.environ["TOKEN_ID"], price=0.50, size=10, side=Side.BUY),
    options=PartialCreateOrderOptions(tick_size="0.01", neg_risk=False),
    order_type=OrderType.GTC)
```

The simplest auth path mirrors the docs' L2 example:
`ClobClient(host, chain_id=137, key=PRIVATE_KEY, creds=api_creds, signature_type=3,
funder=DEPOSIT_WALLET_ADDRESS)` then `create_and_post_order(OrderArgs(...),
options=PartialCreateOrderOptions(tick_size, neg_risk))`. Existing Safe/Proxy
users set the matching `signature_type` (0/1/2) and funder. See
`troubleshooting.md` for rejections.
