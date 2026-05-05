from models import CacheSet
from typing import Optional

class ReplacementPolicy:
    name = "base"

    def on_hit(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        raise NotImplementedError

    def choose_victim(self, cache_set: CacheSet, address: int, pc: Optional[int], time_step: int) -> int:
        raise NotImplementedError

    def on_insert(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        raise NotImplementedError