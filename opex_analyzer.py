#!/usr/bin/env python3
"""
opex analyzer: Reads opex.cfg from a remote ZIP file without downloading the entire archive.
Designed by Jerry Tse
"""

import argparse
import json
import sys
from remotezip import RemoteZip

def analyze_opex_from_url(url: str):
    """Extract and analyze opex.cfg directly from a remote ZIP."""
    try:
        with RemoteZip(url) as rz:
            # List all files in the ZIP, find opex.cfg
            file_list = rz.namelist()
            cfg_path = None
            for name in file_list:
                if name.endswith('opex.cfg'):   # supports root or subdirectory
                    cfg_path = name
                    break

            if not cfg_path:
                print("Error: opex.cfg not found in the ZIP file", file=sys.stderr)
                sys.exit(1)

            # Read only that file's content
            with rz.open(cfg_path) as f:
                cfg_data = f.read().decode('utf-8')

            # Parse JSON
            try:
                cfg = json.loads(cfg_data)
            except json.JSONDecodeError as e:
                print(f"Error: opex.cfg is not valid JSON\n{e}", file=sys.stderr)
                sys.exit(1)

            # Extract businessCode
            business_code = cfg.get('businessCode', '')

            # Extract ovlMountPath from ovlList
            ovl_list = cfg.get('ovlList', [])
            ovl_paths = [item.get('ovlMountPath', '') for item in ovl_list if item.get('ovlMountPath')]

            if not business_code and not ovl_paths:
                print("Warning: businessCode or ovlMountPath fields not found")

            # Format output (consistent with the original Bash script)
            if business_code and ovl_paths:
                if len(ovl_paths) == 1:
                    path_str = f'"{ovl_paths[0]}"'
                else:
                    # Join with commas and " and " for the last one
                    quoted = [f'"{p}"' for p in ovl_paths]
                    path_str = ', '.join(quoted[:-1]) + f' and {quoted[-1]}'
                print(f'\n"{business_code}" is used to fix issues with {path_str}')
            else:
                print("Unable to generate complete analysis result")

            # Show details
            print("\nDetails:")
            print(f"Opex Code: {business_code}")
            print(f"ovlList count: {len(ovl_paths)}")
            if ovl_paths:
                print("ovlMountPath list:")
                for p in ovl_paths:
                    print(f"  - {p}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        # Common failure: server does not support Range requests
        if '416' in str(e) or 'range' in str(e).lower():
            print("Hint: The remote server may not support Range requests, partial download unavailable.", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Opex Analyzer Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python3 %(prog)s <URL>
"""
    )
    parser.add_argument('url', help='URL to resolve')
    args = parser.parse_args()

    url = args.url
    
    if not url:
        print("Error: link cannot be empty", file=sys.stderr)
        sys.exit(1)

    analyze_opex_from_url(url)
    print("\nAnalysis completed!")

if __name__ == '__main__':
    main()