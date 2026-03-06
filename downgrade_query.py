#!/usr/bin/env python3
"""
ColorOS Downgrade Query Tool
Designed by Jerry Tse
"""

import sys
import os
import json
import base64
import time
from typing import Dict, Optional

import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# --- Configuration ---

URL = "https://downgrade.coloros.com/downgrade/query-v3"
NEGOTIATION_VERSION = 1636449646204

REAL_PUB_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmeQzr0TIbtwZFnDXgatg
6xP9SlNBFho1NTdFQ27SKDF+dBEEfnG9BqRw0na0DUqtpWe2CUtldbU33nnJ0KB6
z7y5f+89o9n8mJxIbh952gpskBxyrhCfpYHV5mt/n9Tkm8OcQWLRFou7/XITuZeZ
ejfUTesQjpfOeCaeKyVSoKQc6WuH7NSYq6B37RMyEn/1+vo8XuHEKD84p29KGpyG
I7ZeL85iOcwBmOD6+e4yideH2RatA1SzEv/9V8BflaFLAWDuPWUjA2WgfOvy5spY
mp/MoMOX4P0d+AkJ9Ms6PUXEUBsbOACmaMFyLCLHmd18+UeGdJR/3I15sXKbJhKe
rwIDAQAB
-----END PUBLIC KEY-----"""

# --- Crypto Helpers ---

def get_protected_key(session_key_bytes: bytes) -> str:
    pub_key = serialization.load_pem_public_key(REAL_PUB_KEY.encode(), backend=default_backend())
    rsa_input = base64.b64encode(session_key_bytes)
    encrypted_bytes = pub_key.encrypt(
        rsa_input,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None)
    )
    return base64.b64encode(encrypted_bytes).decode()

def encrypt_aes_gcm(plaintext: str, key: bytes, iv: bytes) -> Dict[str, str]:
    encryptor = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()).encryptor()
    ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
    return {
        "cipher": base64.b64encode(ciphertext + encryptor.tag).decode(),
        "iv": base64.b64encode(iv).decode()
    }

def decrypt_aes_gcm(cipher_b64: str, iv_b64: str, key: bytes) -> Optional[bytes]:
    try:
        full_cipher = base64.b64decode(cipher_b64)
        iv = base64.b64decode(iv_b64)
        tag, ciphertext = full_cipher[-16:], full_cipher[:-16]
        decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    except Exception:
        return None

def print_usage():
    print("\nUsage:")
    print(f"  python3 {sys.argv[0]} <OTA_Prefix> <PrjNum> <snNum> <DUID> [--debug 0|1]")
    print("\nConstraints:")
    print("  <OTA_Prefix> : Must contain at least one '_' (e.g., PKX110_11.C)")
    print("  <PrjNum>     : Must be exactly 5 digits (e.g., 24821)")
    print("  <snNum>      : SN Number from device (e.g., a1b2c3d4)")
    print("  <DUID>       : Must be a 64-character SHA256 string (get from *#6776#)")
    print("\nOptions:")
    print("  --debug 0|1  : Enable (1) or disable (0) debug output (prints metadata if available)")
    print("\nExamples:")
    print(f"  python3 {sys.argv[0]} PKX110_11.C 24821 a1b2c3d4 498A44DF1BEC4EB19FBCB3A870FCACB4EC7D424979CC9C517FE7B805A1937746")
    print(f"  python3 {sys.argv[0]} PKX110_11.C 24821 a1b2c3d4 498A44DF1BEC4EB19FBCB3A870FCACB4EC7D424979CC9C517FE7B805A1937746 --debug 1")

# --- Main Logic ---

def main():
    # Argument parsing: support 5 args (no debug) or 7 args (with --debug value)
    if len(sys.argv) not in (5, 7):
        print_usage()
        sys.exit(1)

    debug = 0
    if len(sys.argv) == 7:
        if sys.argv[5] != "--debug":
            print(f"\n❌ Error: Expected '--debug' at position 5, got '{sys.argv[5]}'")
            print_usage()
            sys.exit(1)
        debug_value = sys.argv[6]
        if debug_value not in ("0", "1"):
            print(f"\n❌ Error: --debug value must be 0 or 1, got '{debug_value}'")
            sys.exit(1)
        debug = int(debug_value)
        ota_version = sys.argv[1].upper()
        prj_num = sys.argv[2]
        sn_num = sys.argv[3]
        duid = sys.argv[4]
    else:  # 5 args
        ota_version = sys.argv[1].upper()
        prj_num = sys.argv[2]
        sn_num = sys.argv[3]
        duid = sys.argv[4]

    # Validate arguments
    if "_11." not in ota_version:
        print(f"\n❌ Error: Argument 1 (OTA_Prefix) '{ota_version}' must contain an underscore '_'.")
        sys.exit(1)

    if not prj_num.isdigit() or len(prj_num) != 5:
        print(f"\n❌ Error: Argument 2 (PrjNum) '{prj_num}' must be exactly 5 digits.")
        sys.exit(1)

    if len(duid) != 64:
        print(f"\n❌ Error: Argument 3 (DUID) length is {len(duid)}, expected 64 characters.")
        sys.exit(1)

    model = ota_version.split("_")[0]
    requests.packages.urllib3.disable_warnings()

    print(f"Querying downgrade for {ota_version}\n")

    carriers = ["10010111", "10011000"]

    for idx, current_carrier in enumerate(carriers):
        session_key = os.urandom(32)
        iv = os.urandom(12)

        try:
            protected_key = get_protected_key(session_key)
            encrypted_device_id_obj = encrypt_aes_gcm(duid, session_key, iv)
            
            payload = {
                "model": model,
                "nvCarrier": current_carrier,
                "prjNum": prj_num,
                "serialNo": sn_num,
                "otaVersion": ota_version,
                "deviceId": encrypted_device_id_obj
            }

            cipher_info = {
                "downgrade-server": {
                    "negotiationVersion": NEGOTIATION_VERSION,
                    "protectedKey": protected_key,
                    "version": str(int(time.time()))
                }
            }

            headers = {
                "Host": "downgrade.coloros.com",
                "Content-Type": "application/json; charset=UTF-8",
                "cipherInfo": json.dumps(cipher_info),
                "deviceId": duid,
                "Connection": "close"
            }

            resp = requests.post(URL, headers=headers, json=payload, timeout=20, verify=False)

            if resp.status_code == 200:
                resp_json = resp.json()
                
                if isinstance(resp_json, dict) and resp_json.get('code') == 1004:
                    print("DUID query GUID is empty")
                    return

                final_data = None
                if "cipher" in resp_json:
                    decrypted_bytes = decrypt_aes_gcm(resp_json["cipher"], resp_json["iv"], session_key)
                    if decrypted_bytes:
                        try: final_data = json.loads(decrypted_bytes)
                        except: pass
                else:
                    final_data = resp_json

                if final_data:
                    has_data = False
                    if "data" in final_data and final_data["data"]:
                        pkg_list = final_data["data"].get("downgradeVoList")
                        if pkg_list:
                            has_data = True
                            for i, pkg in enumerate(pkg_list):
                                print("Fetch Info:")
                                print(f"• Link: {pkg.get('downloadUrl', 'N/A')}")
                                print(f"• Changelog: {pkg.get('versionIntroduction', 'N/A')}")
                                print(f"• Version: {pkg.get('colorosVersion', '')} ({pkg.get('androidVersion', '')})")
                                print(f"• Ota Version: {pkg.get('otaVersion', 'N/A')}")
                                print(f"• MD5: {pkg.get('fileMd5', 'N/A')}")
                                file_size = pkg.get('fileSize')
                                if file_size is not None:
                                    try:
                                        size_mb = int(file_size) / 1024 / 1024
                                        print(f"• File Size: {file_size} Byte ({size_mb:.0f}M)")
                                    except: print(f"• File Size: {file_size} Byte (N/A)")
                                else: print("• File Size: N/A")
                                if i < len(pkg_list) - 1 or debug: print()

                            if debug == 1 and final_data['data'].get('metaData'):
                                print(f"Metadata:\n{final_data['data']['metaData']}")
                            
                            return
                            
                    if idx == 0:
                        time.sleep(1)
                        continue
                    else:
                        print("No Downgrade Package")
                else:
                    print("No Downgrade Package")
            
            else:
                if idx == 0:
                    time.sleep(1)
                    continue
                print(f"[!] Server returned HTTP {resp.status_code}")

        except Exception as e:
            if idx == 0: 
                time.sleep(1.5)
                continue
            print(f"[!] Error: {e}")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
