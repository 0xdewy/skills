---
name: smartcontract-poc
description: >-
  Set up smart contract proof-of-concept environments using Immunefi bug bounty
  scope data. Use when the user wants to scrape contract addresses or GitHub
  repos from an Immunefi bug bounty program, generate Foundry POC templates
  from on-chain contracts, or prepare a security research workspace for a
  specific protocol. TRIGGER on: "immunefi", "bug bounty", "POC setup", "contract addresses", "smart contract POC", "foundry POC", "scrape immunefi", "setup poc for X", "get in-scope contracts".
  SKIP on: "what is immunefi", "how do bug bounties work", "general blockchain education", "non-security research contexts".
license: MIT
metadata:
  author: iamky1e
  version: 1.0.0
  category: security
  tags:
    - smart-contracts
    - immunefi
    - foundry
    - poc
    - security-research
    - bug-bounty
---

# Smart Contract POC

Two scripts that work together: `scrape_immunefi.py` pulls in-scope contract addresses and GitHub repos from Immunefi, then `quickpoc.sh` generates ready-to-run Foundry POC sandboxes from those addresses.

`$SKILL_DIR` = the directory containing this SKILL.md file.

## Required Environment Variables

The user must have these exported in their shell:

- `ETHERSCAN_API_KEY` — Etherscan API key (free at etherscan.io)
- `ETH_RPC_URL` — Ethereum RPC endpoint URL (e.g. Alchemy, Infura)

Do NOT source `.env` or `.bashrc` files — rely on inherited environment.

## Required Tools

- `python3` with `requests` and `beautifulsoup4` (`pip install requests beautifulsoup4`)
- `forge` and `cast` (Foundry toolchain)
- `jq`
- `curl`
- `playwright` (optional fallback for scraping, `pip install playwright && playwright install chromium`)

## Workflow

### Step 1: Scrape Immunefi (optional — user can also provide addresses directly)

```bash
python3 $SKILL_DIR/scripts/scrape_immunefi.py --project <slug> --chain <chain> [--repos]
```

- `--project` — Immunefi project slug (e.g. `layerzero`, `aave`, `uniswap`)
- `--chain` — Chain name or alias (e.g. `ethereum`, `eth`, `bsc`, `arbitrum`)
- `--repos` — Also scrape GitHub repos from the resources page
- `-o <file>` — Custom output filename (default: `{project}_{chain}.txt`)
- `--repos-output <file>` — Custom repos output filename (default: `{project}_repos.txt`)
- `--force-playwright` — Use headless browser instead of HTTP requests

This creates:
- `{project}_{chain}.txt` — one contract address per line
- `{project}_repos.txt` — one GitHub repo URL per line (if `--repos`)

### Step 2: Generate Foundry POC

```bash
# Single address
$SKILL_DIR/scripts/quickpoc.sh 0xAddress [folder_name]

# From addresses file
$SKILL_DIR/scripts/quickpoc.sh -f layerzero_ethereum.txt [folder_name]
```

Folder is optional — if omitted, it auto-derives from the first contract's on-chain name.

**Limitation**: `quickpoc.sh` currently only supports Ethereum mainnet (hardcoded `chainid=1` Etherscan API calls). For other chains, use the addresses file from `scrape_immunefi.py` and set up the forge project manually with the appropriate explorer API URL.

This creates a Foundry project with:
- `src/` populated with verified contract source code from Etherscan
- Proxy detection (resolves implementation via EIP-1967 storage slot)
- Auto-generated test file with mainnet forking setup
- Correct Solidity pragma detection
- Library remappings
- `cd <folder>` copied to clipboard

### Step 3: Run POC

```bash
cd <folder>
forge test -vvvv
```

Edit the test file to interact with the contract and reproduce vulnerabilities.

## Chain Aliases

`scrape_immunefi.py` supports these chain names/aliases: ethereum/eth/mainnet, bsc/bnb, avalanche/avax, arbitrum/arb, polygon/matic, optimism/op, fantom/ftm, base, gnosis/xdai, celo, harmony, aurora, conflux, moonbeam, injective, kava, fuse, canto, blast, fraxtal, horizen, klaytn, core, astar, zksync, linea, scroll, mantle, telos, dos.

## Examples

```bash
# Full workflow: scrape LayerZero scope + generate POC
python3 $SKILL_DIR/scripts/scrape_immunefi.py --project layerzero --chain ethereum --repos
$SKILL_DIR/scripts/quickpoc.sh -f layerzero_ethereum.txt

# Quick POC from a single address
$SKILL_DIR/scripts/quickpoc.sh 0x66A71Dcef29A0fFBDBE3c6a460a3B5BC225Cd675

# Scrape addresses only
python3 $SKILL_DIR/scripts/scrape_immunefi.py --project aave --chain ethereum

# Scrape repos only
python3 $SKILL_DIR/scripts/scrape_immunefi.py --project uniswap --repos

# Force Playwright browser (if requests phase finds nothing)
python3 $SKILL_DIR/scripts/scrape_immunefi.py --project curve --chain ethereum --force-playwright
```
