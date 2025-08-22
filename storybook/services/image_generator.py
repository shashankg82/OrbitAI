


import os
from pathlib import Path
import requests

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HF_TOKEN = "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"  # set via environment
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

class ImageGenError(Exception):
    pass

def generate_images(prompt: str, output_path: str, timeout: int = 120) -> str:
    if not HF_TOKEN:
        raise ImageGenError("HF_TOKEN not set in environment variables.")

    resp = requests.post(
        API_URL,
        headers=HEADERS,
        json={"inputs": prompt},
        timeout=timeout,
    )

    
    ctype = resp.headers.get("content-type", "")
    if resp.ok and ctype.startswith("image/"):
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        if out_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            out_path = out_path.with_suffix(".png")
        out_path.write_bytes(resp.content)
        return str(out_path)

    
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text[:500]

    raise ImageGenError(f"HF API error [{resp.status_code}]: {detail}")
