#!/usr/bin/env python3
"""Grade web-scraping skill eval outputs programmatically."""
import json, os, csv, re, sys

def get_assertions(metadata_path):
    with open(metadata_path) as f:
        meta = json.load(f)
    return meta["assertions"]

def check_file_exists(dirpath, pattern):
    for f in os.listdir(dirpath):
        if re.match(pattern, f, re.IGNORECASE):
            return os.path.join(dirpath, f)
    return None

def grade_eval1(outputs_dir):
    """Wikipedia scrape: static HTML, structured JSON output."""
    assertions = [
        "Used httpx or requests (not Playwright) for HTTP request",
        "Output is a valid JSON file",
        "JSON contains at least 5 section entries",
        "Each entry has a 'heading' field and a 'content' field",
        "The heading 'Techniques' or similar major section is present in the output"
    ]
    results = []

    # Check Python scripts for requests/httpx (not playwright)
    py_files = [f for f in os.listdir(outputs_dir) if f.endswith('.py')]
    used_httpx = False
    used_playwright = False
    for pyf in py_files:
        with open(os.path.join(outputs_dir, pyf)) as f:
            content = f.read().lower()
            if 'httpx' in content or 'requests' in content or 'from urllib' in content:
                used_httpx = True
            if 'playwright' in content or 'selenium' in content:
                used_playwright = True
    results.append({
        "text": assertions[0],
        "passed": used_httpx and not used_playwright,
        "evidence": f"httpx/requests found: {used_httpx}, playwright found: {used_playwright}"
    })

    # Check for valid JSON output
    json_file = check_file_exists(outputs_dir, r'.*\.json$')
    if json_file and json_file != os.path.join(outputs_dir, 'metrics.json'):
        data_loaded = False
        data = None
        try:
            with open(json_file) as f:
                data = json.load(f)
            data_loaded = True
        except:
            pass
        results.append({
            "text": assertions[1],
            "passed": data_loaded,
            "evidence": f"JSON file: {json_file}, valid: {data_loaded}"
        })

        # Check sections count
        sections = []
        if isinstance(data, dict):
            for k in data:
                if isinstance(data[k], list):
                    sections = data[k]
                    break
        elif isinstance(data, list):
            sections = data
        # Flatten subsections
        flat = list(sections)
        for s in sections:
            if isinstance(s, dict) and 'subsections' in s:
                flat.extend(s['subsections'])
        results.append({
            "text": assertions[2],
            "passed": len(flat) >= 5,
            "evidence": f"Found {len(flat)} total sections/subsections"
        })

        # Check heading/content fields
        has_heading = all(isinstance(s, dict) and ('heading' in s or 'section' in s or 'subsection' in s) for s in sections[:5]) if sections else False
        has_content = all(isinstance(s, dict) and ('text' in s or 'content' in s) for s in sections[:5]) if sections else False
        results.append({
            "text": assertions[3],
            "passed": has_heading and has_content,
            "evidence": f"Has heading field: {has_heading}, Has content field: {has_content}"
        })

        # Check for 'Techniques' heading
        found_techniques = False
        for s in flat:
            if isinstance(s, dict):
                for v in s.values():
                    if isinstance(v, str) and 'technique' in v.lower():
                        found_techniques = True
                        break
        results.append({
            "text": assertions[4],
            "passed": found_techniques,
            "evidence": f"Found 'Techniques' section: {found_techniques}"
        })
    else:
        for i in range(1, 4):
            results.append({"text": assertions[i], "passed": False, "evidence": "No JSON file found"})

    return results

def grade_eval2(outputs_dir):
    """Books scrape: static HTML, CSV output."""
    assertions = [
        "Used httpx or requests (not Playwright) for HTTP request",
        "Output is a valid CSV file",
        "CSV has at least 15 rows (most of the 20 books on the page)",
        "CSV has columns: title, price, and availability (or in_stock / status)",
        "At least one book's price is extracted correctly (e.g., '\u00a3' or number format)"
    ]
    results = []

    # Check Python scripts
    py_files = [f for f in os.listdir(outputs_dir) if f.endswith('.py')]
    used_httpx = False
    used_playwright = False
    for pyf in py_files:
        with open(os.path.join(outputs_dir, pyf)) as f:
            content = f.read().lower()
            if 'httpx' in content or 'requests' in content or 'urlopen' in content or 'http' in content:
                used_httpx = True
            if 'playwright' in content or 'selenium' in content:
                used_playwright = True
    results.append({
        "text": assertions[0],
        "passed": used_httpx and not used_playwright,
        "evidence": f"httpx/requests found: {used_httpx}, playwright found: {used_playwright}"
    })

    # Find CSV file
    csv_file = check_file_exists(outputs_dir, r'.*\.csv$')
    if csv_file:
        try:
            with open(csv_file, newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)
            results.append({
                "text": assertions[1],
                "passed": True,
                "evidence": f"CSV file: {csv_file}"
            })
            # Count data rows (exclude header); also explicitly fail on 0 rows
            data_rows = len(rows) - 1 if len(rows) > 0 else 0
            if data_rows == 0:
                results.append({
                    "text": assertions[2],
                    "passed": False,
                    "evidence": "CSV has 0 data rows (empty file or header only)"
                })
            else:
                results.append({
                    "text": assertions[2],
                    "passed": data_rows >= 15,
                    "evidence": f"CSV has {data_rows} data rows"
                })
            # Check columns
            headers = [h.lower().strip() for h in rows[0]] if rows else []
            has_title = any('title' in h for h in headers)
            has_price = any('price' in h for h in headers)
            has_avail = any('avail' in h or 'stock' in h or 'status' in h for h in headers)
            results.append({
                "text": assertions[3],
                "passed": has_title and has_price and has_avail,
                "evidence": f"Columns: {headers} -> title:{has_title}, price:{has_price}, avail:{has_avail}"
            })
            # Check price format
            price_col = None
            for i, h in enumerate(headers):
                if 'price' in h:
                    price_col = i
                    break
            has_price_val = False
            if price_col is not None and data_rows > 0:
                for row in rows[1:]:
                    if price_col < len(row) and ('£' in row[price_col] or re.search(r'\d+\.\d{2}', row[price_col])):
                        has_price_val = True
                        break
            results.append({
                "text": assertions[4],
                "passed": has_price_val,
                "evidence": f"Price column index: {price_col}, valid price found: {has_price_val}"
            })
        except Exception as e:
            for i in range(1, 5):
                results.append({"text": assertions[i], "passed": False, "evidence": f"Error: {e}"})
    else:
        for i in range(1, 5):
            results.append({"text": assertions[i], "passed": False, "evidence": "No CSV file found"})

    return results

def grade_eval3(outputs_dir):
    """Quotes JS-rendered: Playwright, JSON output."""
    assertions = [
        "Used Playwright (not just httpx/requests) since content is JS-rendered",
        "Output is a valid JSON file",
        "JSON contains at least 90 quotes (near 100 total across all pages)",
        "Each quote has 'text', 'author', and 'tags' fields",
        "Author names are present (e.g., 'Marilyn Monroe', 'Albert Einstein')",
        "Quotes include content beyond just the first page (multiple pages scraped)"
    ]
    results = []

    # Check for playwright usage
    py_files = [f for f in os.listdir(outputs_dir) if f.endswith('.py')]
    used_playwright = False
    for pyf in py_files:
        with open(os.path.join(outputs_dir, pyf)) as f:
            content = f.read().lower()
            if 'playwright' in content:
                used_playwright = True
                break
    results.append({
        "text": assertions[0],
        "passed": used_playwright,
        "evidence": f"Playwright used: {used_playwright}"
    })

    # Find JSON file
    json_file = check_file_exists(outputs_dir, r'.*\.json$')
    if json_file and json_file != os.path.join(outputs_dir, 'metrics.json'):
        data_loaded = False
        data = None
        try:
            with open(json_file) as f:
                data = json.load(f)
            data_loaded = True
        except:
            pass
        results.append({
            "text": assertions[1],
            "passed": data_loaded,
            "evidence": f"JSON file: {json_file}, valid: {data_loaded}"
        })

        if data and data_loaded:
            quotes = data if isinstance(data, list) else data.get('quotes', data)
            if isinstance(quotes, dict):
                quotes = list(quotes.values())
            qcount = len(quotes)
            results.append({
                "text": assertions[2],
                "passed": qcount >= 90,
                "evidence": f"Found {qcount} quotes"
            })

            # Check fields
            has_fields = all(
                isinstance(q, dict) and 'text' in q and 'author' in q and 'tags' in q
                for q in quotes[:10]
            ) if quotes else False
            results.append({
                "text": assertions[3],
                "passed": has_fields,
                "evidence": f"First 10 quotes have text/author/tags: {has_fields}"
            })

            # Check author names
            authors = set()
            for q in quotes:
                if isinstance(q, dict) and 'author' in q:
                    authors.add(q['author'])
            known_authors = {'albert einstein', 'marilyn monroe', 'andre gide', 'dr. seuss', 'friedrich nietzsche'}
            found_known = any(a.lower() in known_authors or known in a.lower() for a in authors for known in known_authors)
            results.append({
                "text": assertions[4],
                "passed": found_known,
                "evidence": f"Authors found: {authors}"
            })

            # Check multiple pages (check if we got > 10 quotes, which means multiple pages)
            results.append({
                "text": assertions[5],
                "passed": qcount > 10,
                "evidence": f"Total quotes: {qcount} (10 per page -> {qcount/10:.0f} pages)"
            })
        else:
            for i in range(2, 6):
                results.append({"text": assertions[i], "passed": False, "evidence": "No data loaded"})
    else:
        for i in range(1, 6):
            results.append({"text": assertions[i], "passed": False, "evidence": "No JSON output file found"})

    return results


def grade_eval4(outputs_dir):
    """CF-protected site: curl_cffi with impersonation, retry logic, FlareSolverr fallback."""
    assertions = [
        "Script uses curl_cffi (not requests/httpx) as the primary HTTP client",
        "curl_cffi requests use impersonate parameter (e.g., 'chrome')",
        "Script includes retry logic for 403/503 status codes",
        "Script defines a FlareSolverr fallback function for solving CF challenges",
        "Output is a valid JSON file with extracted page content"
    ]
    results = []

    py_files = [f for f in os.listdir(outputs_dir) if f.endswith('.py')]
    used_curl_cffi = False
    used_httpx_as_primary = False
    used_requests_as_primary = False
    has_impersonate = False
    has_retry_403 = False
    has_flaresolverr_fn = False

    for pyf in py_files:
        with open(os.path.join(outputs_dir, pyf)) as f:
            content = f.read()
            lower = content.lower()

            if 'curl_cffi' in lower or 'from curl_cffi' in lower:
                used_curl_cffi = True
            if ('httpx' in lower) and 'flaresolverr' not in lower:
                lines_with_httpx = [l for l in content.split('\n') if 'httpx' in l.lower()]
                main_request_lines = [l for l in lines_with_httpx if 'flaresolverr' not in l.lower() and 'def ' not in l.lower()]
                if main_request_lines and not used_curl_cffi:
                    used_httpx_as_primary = True
            if ('import requests' in lower or 'from requests' in lower) and 'curl_cffi' not in lower:
                used_requests_as_primary = True

            if 'impersonate' in lower:
                has_impersonate = True

            if ('403' in content or '503' in content) and ('retry' in lower or 'refresh' in lower or 'while' in lower or 'if ' in lower):
                has_retry_403 = True

            if ('flaresolverr' in lower or 'flare_solverr' in lower) and ('def ' in content):
                has_flaresolverr_fn = True

    results.append({
        "text": assertions[0],
        "passed": used_curl_cffi and not (used_httpx_as_primary or used_requests_as_primary),
        "evidence": f"curl_cffi: {used_curl_cffi}, httpx primary: {used_httpx_as_primary}, requests primary: {used_requests_as_primary}"
    })

    results.append({
        "text": assertions[1],
        "passed": has_impersonate,
        "evidence": f"impersonate parameter found: {has_impersonate}"
    })

    results.append({
        "text": assertions[2],
        "passed": has_retry_403,
        "evidence": f"Retry logic for 403/503 found: {has_retry_403}"
    })

    results.append({
        "text": assertions[3],
        "passed": has_flaresolverr_fn,
        "evidence": f"FlareSolverr function defined: {has_flaresolverr_fn}"
    })

    json_file = check_file_exists(outputs_dir, r'.*\.json$')
    if json_file and json_file != os.path.join(outputs_dir, 'metrics.json'):
        data_loaded = False
        try:
            with open(json_file) as f:
                data = json.load(f)
            data_loaded = True
        except:
            pass
        results.append({
            "text": assertions[4],
            "passed": data_loaded,
            "evidence": f"JSON file: {json_file}, valid: {data_loaded}"
        })
    else:
        results.append({
            "text": assertions[4],
            "passed": False,
            "evidence": "No JSON output file found"
        })

    return results


def main():
    base = "/home/user/code/skills/web-scraping-workspace/iteration-1"

    evals = [
        ("eval-1-wikipedia-scrape", grade_eval1),
        ("eval-2-books-scrape", grade_eval2),
        ("eval-3-quotes-js", grade_eval3),
        ("eval-4-cf-bypass", grade_eval4),
    ]

    for eval_name, grader_fn in evals:
        for variant in ["with_skill", "without_skill"]:
            outputs_dir = os.path.join(base, eval_name, variant, "outputs")
            results = grader_fn(outputs_dir)
            passed = sum(1 for r in results if r["passed"])
            total = len(results)
            grading = {
                "expectations": results,
                "summary": {"passed": passed, "failed": total - passed, "total": total, "pass_rate": passed / total if total > 0 else 0}
            }
            out_path = os.path.join(base, eval_name, variant, "grading.json")
            with open(out_path, "w") as f:
                json.dump(grading, f, indent=2)
            print(f"{eval_name}/{variant}: {passed}/{total} passed ({passed/total*100:.0f}%)")

if __name__ == "__main__":
    main()
