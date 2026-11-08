import argparse
import base64
import hashlib
import hmac
import json
import os
import time
import uuid

import requests
from dotenv import load_dotenv

load_dotenv()

SWITCHBOT_BASE_URL = "https://api.switch-bot.com"


def require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


class Switchbot:
    def __init__(self, token: str, secret: str):
        self.token = token
        self.secret = secret

    def generate_sign(self):
        nonce = str(uuid.uuid4())
        t = int(round(time.time() * 1000))
        string_to_sign = f"{self.token}{t}{nonce}".encode("utf-8")
        secret = self.secret.encode("utf-8")
        sign = base64.b64encode(
            hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest()
        )

        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "charset": "utf8",
            "t": str(t),
            "sign": str(sign, "utf-8"),
            "nonce": nonce,
        }
        return headers

    def request(self, method: str, path: str, json_data=None, params=None):
        url = SWITCHBOT_BASE_URL + path
        try:
            response = requests.request(
                method,
                url,
                headers=self.generate_sign(),
                json=json_data,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"SwitchBot API request failed: {e}") from e

        try:
            result = response.json() if response.content else {}
        except requests.exceptions.JSONDecodeError as e:
            raise RuntimeError(f"SwitchBot API returned invalid JSON: {e}") from e

        if isinstance(result, dict):
            status_code = result.get("statusCode")
            if status_code is not None and status_code != 100:
                message = result.get("message") or "no error message provided"
                raise RuntimeError(
                    f"SwitchBot API returned statusCode {status_code}: {message}"
                )
        return result

    def get_device_list(self, device_list_path="deviceList.json"):
        result = self.request("GET", "/v1.1/devices")
        with open(device_list_path, mode="wt", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    def get_device_status(self, device_id: str):
        return self.request("GET", f"/v1.1/devices/{device_id}/status")

    def configure_webhook(self, url: str, device_list: str = "ALL"):
        return self.request(
            "POST",
            "/v1.1/webhook/setupWebhook",
            json_data={"action": "setupWebhook", "url": url, "deviceList": device_list},
        )

    def query_webhook(self, url: str | None = None):
        if url is not None:
            payload = {"action": "queryDetails", "urls": [url]}
        else:
            payload = {"action": "queryUrl"}
        return self.request("POST", "/v1.1/webhook/queryWebhook", json_data=payload)

    def update_webhook(self, url: str):
        return self.request(
            "POST",
            "/v1.1/webhook/updateWebhook",
            json_data={
                "action": "updateWebhook",
                "config": {"url": url, "enable": True},
            },
        )

    def delete_webhook(self, url: str):
        return self.request(
            "POST",
            "/v1.1/webhook/deleteWebhook",
            json_data={"action": "deleteWebhook", "url": url},
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SwitchBot webhook and device API helper")
    parser.add_argument(
        "action",
        nargs="?",
        choices=["list", "status", "setup-webhook", "query-webhook", "update-webhook", "delete-webhook"],
        default="status",
    )
    parser.add_argument("--device-id", help="SwitchBot device ID")
    parser.add_argument("--url", help="Webhook URL")
    args = parser.parse_args()

    try:
        token = require_env("SWITCHBOT_TOKEN")
        secret = require_env("SWITCHBOT_SECRET")
    except RuntimeError as e:
        print(e)
        raise SystemExit(1)

    client = Switchbot(token, secret)

    try:
        if args.action == "list":
            result = client.get_device_list()
        elif args.action == "status":
            device_id = args.device_id or require_env("SWITCHBOT_Lock_DEVICEID")
            result = client.get_device_status(device_id)
        elif args.action == "query-webhook":
            result = client.query_webhook(args.url)
        else:
            url = args.url or os.getenv("GAS_URL")
            if not url:
                raise RuntimeError("Webhook URL is required. Pass --url or set GAS_URL.")

            if args.action == "setup-webhook":
                result = client.configure_webhook(url)
            elif args.action == "update-webhook":
                result = client.update_webhook(url)
            else:
                result = client.delete_webhook(url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (RuntimeError, OSError) as e:
        print(e)
        raise SystemExit(1)
