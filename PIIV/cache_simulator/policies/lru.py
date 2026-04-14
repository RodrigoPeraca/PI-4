from .base import ReplacementPolicy
from models import CacheSet
from typing import Optional


class LRUPolicy(ReplacementPolicy):
    name = "lru"

    @staticmethod
    def _update_lru(cache_set: CacheSet, accessed_index: int) -> None:
        for idx, line in enumerate(cache_set.lines):
            if not line.valid:
                continue
            if idx == accessed_index:
                line.lru = 0
            else:
                line.lru += 1

    def on_hit(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        self._update_lru(cache_set, line_index)
        cache_set.lines[line_index].last_access_time = time_step
        cache_set.lines[line_index].owner_pc = pc

    def choose_victim(self, cache_set: CacheSet, address: int, pc: Optional[int], time_step: int) -> int:
        for idx, line in enumerate(cache_set.lines):
            if not line.valid:
                return idx
        return max(range(len(cache_set.lines)), key=lambda i: cache_set.lines[i].lru)

    def on_insert(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        self._update_lru(cache_set, line_index)
        cache_set.lines[line_index].last_access_time = time_step
        cache_set.lines[line_index].owner_pc = pc