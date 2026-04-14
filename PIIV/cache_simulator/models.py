from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CacheLine:
    valid: bool = False
    tag: int = -1
    lru: int = 0
    predicted_reuse: float = float('inf')
    last_access_time: Optional[int] = None
    owner_pc: Optional[int] = None


@dataclass
class CacheSet:
    lines: List[CacheLine]