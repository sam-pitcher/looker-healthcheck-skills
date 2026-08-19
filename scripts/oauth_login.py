#!/usr/bin/env python3
"""
Python OAuth PKCE Login for Looker CLI & Agent.
Works with expired/self-signed SSL certificates (e.g. *.dev.looker.com)
where looker-cli's Go HTTP client fails TLS verification.
"""

import os
import sys
import json
import ssl
import base64
import hashlib
import secrets
import urllib.request
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse

CLIENT_ID = "com.looker.cli"
REDIRECT_URI = "http://127.0.0.1:7777"
PORT = 7777

def generate_pkce():
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return code_verifier, code_challenge

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authentication Successful!</h1><p>You can close this tab and return to your terminal.</p>")
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass

def exchange_code_for_token(host: str, code: str, code_verifier: str, verify_ssl: bool = False):
    token_url = f"https://{host}/api/token"
    payload = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier
    }).encode("utf-8")
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    req = urllib.request.Request(token_url, data=payload, headers=headers, method="POST")
    ctx = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()

    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def update_cli_config(host: str, access_token: str, refresh_token: str = ""):
    config_path = os.path.expanduser("~/.config/looker-cli/config.yaml")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    yaml_content = f"""access_token: {access_token}
client_id: {CLIENT_ID}
host: {host}
port: "443"
refresh_token: {refresh_token}
ssl: true
verify_ssl: false
"""
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"✅ Updated {config_path}")

def update_env_file(host: str, access_token: str):
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    # Remove existing LOOKERSDK_BASE_URL and LOOKERSDK_OAUTH_TOKEN
    new_lines = [l for l in lines if not l.startswith("LOOKERSDK_BASE_URL=") and not l.startswith("LOOKERSDK_OAUTH_TOKEN=") and not l.startswith("LOOKER_VERIFY_SSL=")]
    new_lines.append(f"LOOKERSDK_BASE_URL=https://{host}\n")
    new_lines.append(f"LOOKERSDK_OAUTH_TOKEN={access_token}\n")
    new_lines.append("LOOKER_VERIFY_SSL=false\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✅ Updated .env with host https://{host} and active OAuth token")

def main():
    parser = argparse.ArgumentParser(description="OAuth Login for Looker (SSL Insecure Compatible)")
    parser.add_argument("--host", required=True, help="Looker host (e.g. gcplmaster.dev.looker.com)")
    parser.add_argument("--verify-ssl", action="store_true", default=False, help="Verify SSL certificate")
    args = parser.parse_args()

    host = args.host.replace("https://", "").replace("http://", "").rstrip("/")
    code_verifier, code_challenge = generate_pkce()

    auth_url = (
        f"https://{host}/auth?client_id={CLIENT_ID}"
        f"&code_challenge={code_challenge}&code_challenge_method=S256"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&response_type=code&scope=cors_api"
    )

    print(f"\n🔐 Opening browser for OAuth authentication with {host}...")
    print(f"URL: {auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    auth_code = None
    try:
        server = HTTPServer(("127.0.0.1", PORT), OAuthCallbackHandler)
        server.timeout = 60
        print(f"⏳ Waiting for authorization callback on {REDIRECT_URI} (or paste code manually)...")
        while not OAuthCallbackHandler.auth_code:
            server.handle_request()
        auth_code = OAuthCallbackHandler.auth_code
    except Exception as e:
        print(f"⚠️ Local server listener error: {e}")

    if not auth_code:
        redirect_input = input("\nPaste redirected URL or auth code here: ").strip()
        if "code=" in redirect_input:
            auth_code = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_input).query).get("code", [None])[0]
        else:
            auth_code = redirect_input

    if not auth_code:
        print("❌ Error: No authorization code received.")
        sys.exit(1)

    print("\n🔄 Exchanging authorization code for OAuth access token...")
    try:
        token_data = exchange_code_for_token(host, auth_code, code_verifier, verify_ssl=args.verify_ssl)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token", "")
        if not access_token:
            print("❌ Failed to acquire access token:", token_data)
            sys.exit(1)

        print("🎉 Successfully authenticated!")
        update_cli_config(host, access_token, refresh_token)
        update_env_file(host, access_token)
        print("\n✨ Ready! You can now run healthchecks on this instance.")
    except Exception as e:
        print(f"❌ Error exchanging token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
