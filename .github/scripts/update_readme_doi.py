#!/usr/bin/env python3
"""Update README.md with DOI badge."""
import re, sys

doi = sys.argv[1] if len(sys.argv) > 1 else ""
doi_url = sys.argv[2] if len(sys.argv) > 2 else f"https://doi.org/{doi}"

# Extract short DOI for badge
short_doi = doi_url.replace("https://doi.org/", "")
badge = f"[![DOI](https://zenodo.org/badge/DOI/{short_doi}.svg)]({doi_url})"

with open("README.md", "r") as f:
    content = f.read()

if "zenodo.org/badge" in content:
    # Replace existing badge line
    content = re.sub(r"\[!\[DOI\].*", badge, content)
    print("Replaced existing DOI badge")
else:
    # Add after first heading
    lines = content.split("\n", 1)
    content = lines[0] + "\n" + badge + "\n\n" + (lines[1] if len(lines) > 1 else "")
    print("Added DOI badge")

with open("README.md", "w") as f:
    f.write(content)

print(f"README updated with DOI badge: {badge}")
