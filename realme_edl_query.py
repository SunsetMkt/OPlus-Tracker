#!/usr/bin/env python3
"""
Query official EDL packages for Realme
Designed by Jerry Tse
"""

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests


def check_url(url: str) -> Optional[str]:
    try:
        resp = requests.head(url, timeout=2, allow_redirects=True)
        if resp.status_code == 200:
            return url
    except requests.RequestException:
        return None


def query_edl_link(version_name: str, region: str, date_prefix: str) -> Optional[str]:
    from config import REALME_CONFIG

    if region in ("EU", "EUEX", "EEA", "TR"):
        conf = REALME_CONFIG["gdpr"]
    elif region in ("CN", "CH"):
        conf = REALME_CONFIG["domestic"]
    else:
        conf = REALME_CONFIG["export"]

    bucket, server = conf["bucket"], conf["server"]

    version_clean = (
        re.sub(r"^RMX\d+_", "", version_name).replace("(", "").replace(")", "")
    )
    model = version_name.split("_")[0]
    base_url = f"https://{server}/sw/{model}{bucket}_11_{version_clean}_{date_prefix}"

    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [
            executor.submit(check_url, f"{base_url}{i:04d}.zip") for i in range(10000)
        ]
        for future in as_completed(futures):
            found_url = future.result()
            if found_url:
                return found_url

    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Realme EDL Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 %(prog)s "RMX3888_16.0.3.500(CN01)" CN 202601241320
""",
    )
    parser.add_argument(
        "version_name",
        metavar="VERSION_NAME",
        help="Version name (e.g., RMX3888_16.0.3.500(CN01))",
    )
    parser.add_argument(
        "region", metavar="REGION", help="Region code (e.g., CN, EU, IN)"
    )
    parser.add_argument(
        "date", metavar="DATE", help="12-character date prefix (e.g., 202601241320)"
    )
    args = parser.parse_args(argv)

    version_name = args.version_name
    region = args.region.upper()
    date_prefix = args.date

    if len(date_prefix) != 12:
        parser.error(f"Date length is {len(date_prefix)}, expected 12 characters.")

    print(f"Querying for {version_name}\n")

    found_url = query_edl_link(version_name, region, date_prefix)

    print("Fetch Info:")
    if found_url:
        print(f"• Link: {found_url}")
        return 0

    print("• Link: Not Found")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
