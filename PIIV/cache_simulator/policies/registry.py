from .base import ReplacementPolicy
from .lru import LRUPolicy
from .mockingjay import MockingjayLitePolicy

def build_policy(policy_name: str) -> ReplacementPolicy:
    normalized = policy_name.strip().lower()
    if normalized == "lru":
        return LRUPolicy()
    if normalized in {"mockingjay", "mockingjay_lite", "mj"}:
        return MockingjayLitePolicy()
    raise ValueError(f"Política desconhecida: {policy_name}")