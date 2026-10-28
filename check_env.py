"""Run this the moment you get AWS credentials:  python check_env.py
It checks your identity, lists the Bedrock models you can use, and makes one test call."""
import os
import sys

import boto3
from dotenv import load_dotenv

load_dotenv()
region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

try:
    ident = boto3.client("sts", region_name=region).get_caller_identity()
    print(f"[ok] AWS identity: {ident['Arn']}")
except Exception as e:
    sys.exit(f"[x] No working AWS credentials ({e}).\n    Paste the Workshop Studio credentials into .env or run `aws configure`.")

bedrock = boto3.client("bedrock", region_name=region)
try:
    models = bedrock.list_foundation_models(byOutputModality="TEXT")["modelSummaries"]
    print(f"[ok] {len(models)} text models visible in {region}. Chat-capable examples:")
    for m in models:
        if any(p in m["modelId"] for p in ("anthropic", "nova", "llama", "mistral")):
            print("     ", m["modelId"])
except Exception as e:
    print(f"[!] Could not list models: {e}")

try:
    profs = bedrock.list_inference_profiles()["inferenceProfileSummaries"]
    if profs:
        print("[i] Inference profiles (use these ids if a plain model id errors):")
        for p in profs[:15]:
            print("     ", p["inferenceProfileId"])
except Exception:
    pass

model_id = os.getenv("BEDROCK_MODEL_ID")
if not model_id:
    sys.exit("\n[!] Set BEDROCK_MODEL_ID in .env to one of the ids above, then re-run.")

from bedrock_helpers import chat  # noqa: E402

try:
    print("[ok] Test call ->", chat("Say 'ready' in one word.", max_tokens=10).strip())
except Exception as e:
    print(f"[x] Test call failed: {e}\n    Common fixes: request model access in the Bedrock console, "
          "use the inference-profile id, or switch region.")
