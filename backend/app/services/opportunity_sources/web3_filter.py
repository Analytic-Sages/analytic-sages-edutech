from __future__ import annotations

import re

WEB3_NEEDLES = (
    "blockchain",
    "web3",
    "web 3",
    "crypto",
    "ethereum",
    "solana",
    "defi",
    "onchain",
    "on-chain",
    "zero knowledge",
    "zero-knowledge",
    "smart contract",
    "digital assets",
    "tokenization",
    "bitcoin",
    "layer 1",
    "layer-1",
    "layer1",
    "layer 2",
    "layer-2",
    "layer2",
)
ZK_RE = re.compile(r"\bzk\b|\brwa\b")
WHITESPACE_RE = re.compile(r"\s+")


def web3_blob(*parts: object) -> str:
    chunks: list[str] = []
    for part in parts:
        if part is None:
            continue
        if isinstance(part, (list, tuple)):
            chunks.append(web3_blob(*part))
            continue
        text = str(part).strip()
        if text:
            chunks.append(text)
    return WHITESPACE_RE.sub(" ", " ".join(chunks)).strip().lower()


def is_web3_text(*parts: object) -> bool:
    text = web3_blob(*parts)
    if not text:
        return False
    if any(needle in text for needle in WEB3_NEEDLES):
        return True
    return bool(ZK_RE.search(text))
