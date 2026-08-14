"""
Report whether the configured OpenRouter key works, without printing it.

Written for a key rotation. After revoking the old keys and pasting a new one
into .env, the question "is this actually wired up?" otherwise gets answered by
uploading a CV and squinting at whether the prose looks LLM-written -- which is
a poor test, because the rule-based fallback also produces plausible prose. That
ambiguity is the whole reason this check exists.

    python scripts/check_llm_key.py

Queries GET /api/v1/key, which returns the key's label, usage and limits. It
costs no generation tokens and no daily quota, so it is safe to run repeatedly
during a rotation.

The key is read from the environment, never printed, and never written
anywhere. Output shows a masked prefix only -- enough to confirm which key is
loaded, not enough to use it.
"""
from __future__ import annotations

import os
import sys

KEY_ENDPOINT = "https://openrouter.ai/api/v1/key"
ENV_KEY = "OPENROUTER_API_KEY"


def mask(secret: str) -> str:
    if len(secret) < 20:
        return "(too short to be a valid key)"
    return f"{secret[:12]}...{secret[-4:]}"


def main() -> int:
    # load_dotenv so this sees the same .env the application does, rather than
    # only variables exported into the current shell.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    key = (os.getenv(ENV_KEY) or "").strip()

    print(f"LLM_PROVIDER : {provider or '(unset)'}")

    if not key:
        print(f"{ENV_KEY} : (empty)")
        print()
        print("No key configured. Explanations fall back to rule-based, which is")
        print("a supported mode -- the app runs correctly. Paste a key into .env")
        print("to enable LLM-written explanations.")
        return 0

    print(f"{ENV_KEY} : {mask(key)}")

    if not key.startswith("sk-or-"):
        print()
        print("That does not look like an OpenRouter key (expected an sk-or- prefix).")
        return 1

    try:
        import requests
    except ImportError:
        print("\nrequests is not installed; cannot verify. pip install requests")
        return 1

    try:
        response = requests.get(
            KEY_ENDPOINT,
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
    except Exception as e:  # noqa: BLE001 - network, DNS, TLS
        # Deliberately not printing the exception's request context, which can
        # echo the Authorization header.
        print(f"\nCould not reach OpenRouter: {type(e).__name__}")
        return 1

    if response.status_code == 401:
        print()
        print("REVOKED or invalid - OpenRouter rejected this key (401).")
        print("If you have just rotated, paste the new key into .env.")
        return 1

    if response.status_code != 200:
        print(f"\nUnexpected response: HTTP {response.status_code}")
        return 1

    data = response.json().get("data", {})
    limit = data.get("limit")
    usage = data.get("usage")

    print()
    print("LIVE - OpenRouter accepted this key.")
    if data.get("label"):
        print(f"  label          : {data['label']}")
    print(f"  usage          : {usage if usage is not None else 'n/a'}")
    print(f"  credit limit   : {limit if limit is not None else 'unlimited / free tier'}")
    if data.get("is_free_tier") is not None:
        print(f"  free tier      : {data['is_free_tier']}")

    rate = data.get("rate_limit") or {}
    if rate:
        print(f"  rate limit     : {rate.get('requests')} per {rate.get('interval')}")

    if provider != "openrouter":
        print()
        print(f"Note: the key works, but LLM_PROVIDER is '{provider or 'unset'}',")
        print("so it will not be used. Set LLM_PROVIDER=openrouter in .env.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
