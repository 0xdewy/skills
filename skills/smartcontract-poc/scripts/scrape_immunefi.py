#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

EXPLORER_CHAIN_MAP = {
    "etherscan.io": "ethereum",
    "bscscan.com": "bsc",
    "snowtrace.io": "avalanche",
    "arbiscan.io": "arbitrum",
    "polygonscan.com": "polygon",
    "optimistic.etherscan.io": "optimism",
    "ftmscan.com": "fantom",
    "basescan.org": "base",
    "gnosisscan.io": "gnosis",
    "celoscan.io": "celo",
    "moonscan.io": "moonbeam",
    "explorer.harmony.one": "harmony",
    "scope.klaytn.com": "klaytn",
    "explorer.aurora.dev": "aurora",
    "evm.confluxscan.io": "conflux",
    "scan.coredao.org": "core",
    "explorer.celo.org": "celo",
    "astar.subscan.io": "astar",
    "subnets.avax.network": "avalanche",
    "explorer.injective.network": "injective",
    "kavascan.com": "kava",
    "explorer.fuse.io": "fuse",
    "explorer.canto.io": "canto",
    "explorer.blast.io": "blast",
    "fraxscan.com": "fraxtal",
    "explorer.horizen.io": "horizen",
    "scan.manta.network": "manta",
    "lineascan.build": "linea",
    "scrollscan.com": "scroll",
    "era.zksync.network": "zksync",
    "explorer.zksync.io": "zksync",
    "mantlescan.xyz": "mantle",
    "tokiotx.org": "toko",
    "explorer.telos.net": "telos",
    "dosexplorer.com": "dos",
}

CHAIN_ALIASES = {
    "ethereum": "ethereum",
    "eth": "ethereum",
    "mainnet": "ethereum",
    "bsc": "bsc",
    "bnb": "bsc",
    "bnbchain": "bsc",
    "avalanche": "avalanche",
    "avax": "avalanche",
    "arbitrum": "arbitrum",
    "arb": "arbitrum",
    "polygon": "polygon",
    "matic": "polygon",
    "optimism": "optimism",
    "op": "optimism",
    "fantom": "fantom",
    "ftm": "fantom",
    "base": "base",
    "gnosis": "gnosis",
    "xdai": "gnosis",
    "celo": "celo",
    "harmony": "harmony",
    "one": "harmony",
    "aurora": "aurora",
    "conflux": "conflux",
    "moonbeam": "moonbeam",
    "injective": "injective",
    "kava": "kava",
    "fuse": "fuse",
    "canto": "canto",
    "blast": "blast",
    "fraxtal": "fraxtal",
    "horizen": "horizen",
    "klaytn": "klaytn",
    "core": "core",
    "astar": "astar",
    "zksync": "zksync",
    "linea": "linea",
    "scroll": "scroll",
    "mantle": "mantle",
    "telos": "telos",
    "dos": "dos",
}

ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def resolve_chain(chain_input):
    return CHAIN_ALIASES.get(chain_input.lower().strip())


def get_explorer_domains_for_chain(chain):
    return [d for d, c in EXPLORER_CHAIN_MAP.items() if c == chain]


def fetch_page(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def extract_from_html(html, chain):
    domains = get_explorer_domains_for_chain(chain)
    addresses = []
    seen = set()

    soup = BeautifulSoup(html, "html.parser")
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        for domain in domains:
            if domain in href:
                match = re.search(r"/address/(0x[a-fA-F0-9]{40})", href, re.IGNORECASE)
                if match:
                    addr = match.group(1).lower()
                    if addr not in seen:
                        seen.add(addr)
                        addresses.append(addr)
                break

    return addresses


def extract_from_rsc_stream(html, chain):
    domains = get_explorer_domains_for_chain(chain)
    addresses = []
    seen = set()

    rsc_chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html)
    for chunk in rsc_chunks:
        try:
            unescaped = chunk.encode().decode("unicode_escape")
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
        for domain in domains:
            pattern = (
                r"https?://(?:[a-zA-Z0-9.-]+\\.)?"
                + re.escape(domain)
                + r"/address/(0x[a-fA-F0-9]{40})"
            )
            for match in re.finditer(pattern, unescaped, re.IGNORECASE):
                addr = match.group(1).lower()
                if addr not in seen:
                    seen.add(addr)
                    addresses.append(addr)

    return addresses


def extract_github_repos_from_html(html):
    repos = set()

    soup = BeautifulSoup(html, "html.parser")
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].split("?")[0]
        parsed = urlparse(href)
        if parsed.netloc == "github.com":
            repo = _normalize_github_url(parsed.path)
            if repo:
                repos.add(repo)

    return repos


def extract_github_repos_from_rsc(html):
    repos = set()

    rsc_chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html)
    for chunk in rsc_chunks:
        try:
            unescaped = chunk.encode().decode("unicode_escape")
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
        for match in re.finditer(r'https://github\.com(/[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*)', unescaped):
            repo = _normalize_github_url(match.group(1))
            if repo:
                repos.add(repo)

    return repos


def _normalize_github_url(path):
    path = path.strip("/")
    if not path:
        return None
    parts = path.split("/")
    if len(parts) < 2:
        return None
    owner = parts[0]
    repo = parts[1]
    if "." in owner and not owner.startswith(" "):
        return None
    return f"https://github.com/{owner}/{repo}"


def scrape_addresses(project, chain):
    url = f"https://immunefi.com/bug-bounty/{project}/scope/"
    html = fetch_page(url)

    addresses = extract_from_html(html, chain)
    rsc_addresses = extract_from_rsc_stream(html, chain)

    seen = set(a.lower() for a in addresses)
    for addr in rsc_addresses:
        if addr.lower() not in seen:
            seen.add(addr.lower())
            addresses.append(addr)

    return addresses


def scrape_repos(project):
    url = f"https://immunefi.com/bug-bounty/{project}/resources/"
    html = fetch_page(url)

    repos = extract_github_repos_from_html(html)
    repos |= extract_github_repos_from_rsc(html)

    return sorted(repos)


def phase2_playwright_addresses(project, chain):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright not installed. Install with: pip install playwright && playwright install chromium")
        return []

    domains = get_explorer_domains_for_chain(chain)
    addresses = []
    seen = set()

    url = f"https://immunefi.com/bug-bounty/{project}/scope/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(8000)

        try:
            show_all = page.locator("button:has-text('Show all')")
            if show_all.count() > 0:
                show_all.first.click()
                page.wait_for_timeout(5000)
        except Exception:
            pass

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        for domain in domains:
            if domain in href:
                match = re.search(r"/address/(0x[a-fA-F0-9]{40})", href, re.IGNORECASE)
                if match:
                    addr = match.group(1).lower()
                    if addr not in seen:
                        seen.add(addr)
                        addresses.append(addr)
                break

    return addresses


def main():
    parser = argparse.ArgumentParser(description="Scrape Immunefi for contract addresses and GitHub repos by project")
    parser.add_argument("--project", required=True, help="Project slug (e.g. layerzero)")
    parser.add_argument("--chain", help="Chain name (e.g. ethereum, bsc, arbitrum)")
    parser.add_argument("--repos", action="store_true", help="Also scrape GitHub repos from the resources page")
    parser.add_argument("--output", "-o", help="Output file for addresses (default: {project}_{chain}.txt)")
    parser.add_argument("--repos-output", help="Output file for repos (default: {project}_repos.txt)")
    parser.add_argument("--force-playwright", action="store_true", help="Skip requests phase, use Playwright directly")
    args = parser.parse_args()

    if not args.chain and not args.repos:
        parser.error("at least one of --chain or --repos is required")

    chain = None
    if args.chain:
        chain = resolve_chain(args.chain)
        if not chain:
            print(f"Unknown chain: {args.chain}")
            print(f"Supported chains: {', '.join(sorted(set(CHAIN_ALIASES.values())))}")
            sys.exit(1)

    if chain:
        addresses = []
        output_file = args.output or f"{args.project}_{chain}.txt"

        if not args.force_playwright:
            print(f"[*] Fetching scope page for '{args.project}' on {chain}...")
            try:
                addresses = scrape_addresses(args.project, chain)
                print(f"[*] Requests: found {len(addresses)} address(es)")
            except Exception as e:
                print(f"[!] Requests failed: {e}")

        if len(addresses) == 0 and not args.force_playwright:
            print("[*] Falling back to Playwright headless browser...")
            try:
                addresses = phase2_playwright_addresses(args.project, chain)
                print(f"[*] Playwright: found {len(addresses)} address(es)")
            except Exception as e:
                print(f"[!] Playwright failed: {e}")

        if args.force_playwright:
            print("[*] Using Playwright headless browser...")
            try:
                addresses = phase2_playwright_addresses(args.project, chain)
                print(f"[*] Playwright: found {len(addresses)} address(es)")
            except Exception as e:
                print(f"[!] Playwright failed: {e}")

        if not addresses:
            print(f"[!] No addresses found for '{args.project}' on {chain}")
        else:
            Path(output_file).write_text("\n".join(addresses) + "\n")
            print(f"[+] Wrote {len(addresses)} address(es) to {output_file}")

    if args.repos:
        repos_output = args.repos_output or f"{args.project}_repos.txt"
        print(f"[*] Fetching resources page for '{args.project}'...")
        try:
            repos = scrape_repos(args.project)
            if not repos:
                print(f"[!] No GitHub repos found for '{args.project}'")
            else:
                Path(repos_output).write_text("\n".join(repos) + "\n")
                print(f"[+] Wrote {len(repos)} repo(s) to {repos_output}")
        except Exception as e:
            print(f"[!] Failed to fetch repos: {e}")


if __name__ == "__main__":
    main()
