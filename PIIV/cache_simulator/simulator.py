from typing import List, Dict, Tuple, Optional
from policies.base import ReplacementPolicy
from models import CacheSet, CacheLine

class CacheSimulator:
    def __init__(self, cache_size: int, block_size: int, associativity: int, policy: ReplacementPolicy):
        if cache_size % (block_size * associativity) != 0:
            raise ValueError(
                "cache_size deve ser múltiplo de block_size * associativity para formar um número inteiro de conjuntos."
            )
        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.num_sets = cache_size // (block_size * associativity)
        self.policy = policy
        self.sets = [CacheSet([CacheLine() for _ in range(associativity)]) for _ in range(self.num_sets)]
        self.hits = 0
        self.misses = 0
        self.time_step = 0

    def decode_address(self, address: int) -> Tuple[int, int]:
        block_number = address // self.block_size
        set_index = block_number % self.num_sets
        tag = block_number // self.num_sets
        return set_index, tag

    def access(self, address: int, pc: Optional[int] = None) -> bool:
        self.time_step += 1
        set_index, tag = self.decode_address(address)
        cache_set = self.sets[set_index]

        for idx, line in enumerate(cache_set.lines):
            if line.valid and line.tag == tag:
                self.hits += 1
                self.policy.on_hit(cache_set, idx, address, pc, self.time_step)
                return True

        self.misses += 1
        victim = self.policy.choose_victim(cache_set, address, pc, self.time_step)
        victim_line = cache_set.lines[victim]
        victim_line.valid = True
        victim_line.tag = tag
        self.policy.on_insert(cache_set, victim, address, pc, self.time_step)
        return False

    def run_trace(self, trace: List[Dict[str, int]]) -> Dict[str, float]:
        for item in trace:
            self.access(item["address"], item.get("pc"))

        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100.0) if total else 0.0
        miss_rate = (self.misses / total * 100.0) if total else 0.0
        return {
            "policy": self.policy.name,
            "cache_size": self.cache_size,
            "block_size": self.block_size,
            "associativity": self.associativity,
            "num_sets": self.num_sets,
            "total_accesses": total,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "miss_rate": miss_rate,
        }