#!/usr/bin/env python3
"""Update CITATION.cff with DOI and version."""
import re, sys

doi = sys.argv[1] if len(sys.argv) > 1 else ""
version = sys.argv[2] if len(sys.argv) > 2 else ""

with open("CITATION.cff", "r") as f:
    content = f.read()

if doi:
    content = re.sub(r'^doi:.*', f'doi: "{doi}"', content, flags=re.MULTILINE)
    print(f"Updated DOI: {doi}")

if version:
    content = re.sub(r'^version:.*', f'version: "{version}"', content, flags=re.MULTILINE)
    print(f"Updated version: {version}")

with open("CITATION.cff", "w") as f:
    f.write(content)

print("CITATION.cff updated")
