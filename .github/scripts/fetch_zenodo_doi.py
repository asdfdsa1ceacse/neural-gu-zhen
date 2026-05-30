#!/usr/bin/env python3
"""Fetch Zenodo DOI for the Neural Gu-Zhen paper."""
import json, urllib.request, sys, time

MAX_RETRIES = 30
RETRY_INTERVAL = 30

for attempt in range(1, MAX_RETRIES + 1):
    print(f"Attempt {attempt}/{MAX_RETRIES}...", file=sys.stderr)
    try:
        url = "https://zenodo.org/api/records?q=Neural+Gu-Zhen&sort=mostrecent&size=5"
        req = urllib.request.Request(url, headers={"User-Agent": "GitHub-Actions"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())

        # Try various response structures
        hits = []
        if isinstance(data, dict):
            hits = data.get("hits", {}).get("hits", data.get("records", []))
        elif isinstance(data, list):
            hits = data

        for record in hits:
            meta = record.get("metadata", record)
            doi = meta.get("doi", record.get("doi", ""))
            if doi:
                conceptdoi = meta.get("conceptdoi", record.get("conceptdoi", ""))
                # Set GitHub Actions outputs
                with open(sys.stdout.fileno() if hasattr(sys.stdout, 'fileno') else None or '/dev/null') as _:
                    pass
                print(f"doi={doi}")
                print(f"url=https://doi.org/{doi}")
                if conceptdoi:
                    print(f"conceptdoi={conceptdoi}")
                print(f"Found DOI: {doi}", file=sys.stderr)
                sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

    time.sleep(RETRY_INTERVAL)

print("doi=UNKNOWN")
print("url=UNKNOWN")
print("Max retries reached, DOI not found", file=sys.stderr)
sys.exit(1)
