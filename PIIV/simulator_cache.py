import argparse
import csv
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


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


class ReplacementPolicy:
    name = "base"

    def on_hit(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        raise NotImplementedError

    def choose_victim(self, cache_set: CacheSet, address: int, pc: Optional[int], time_step: int) -> int:
        raise NotImplementedError

    def on_insert(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        raise NotImplementedError


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


class MockingjayLitePolicy(ReplacementPolicy):
    """
    Versão simplificada inspirada no Mockingjay.

    Ideia usada aqui na Sprint 1:
    - Mantemos um preditor por "assinatura" de PC.
    - A assinatura guarda a média móvel da distância de reuso observada.
    - Em um miss, expulsa-se a linha cuja previsão de próximo reuso é mais distante.

    Isso NÃO é uma implementação fiel do paper original, mas serve como modelagem
    de alto nível para comparar com LRU na fase inicial do projeto.
    """

    name = "mockingjay_lite"

    def __init__(self, alpha: float = 0.5, default_prediction: float = 1000.0):
        self.alpha = alpha
        self.default_prediction = default_prediction
        self.predictor: Dict[int, float] = {}

    def _signature(self, pc: Optional[int], address: int) -> int:
        # Quando não houver PC no traço, usamos uma assinatura simples derivada do endereço.
        if pc is not None:
            return pc
        return address >> 5

    def _predict(self, pc: Optional[int], address: int) -> float:
        sig = self._signature(pc, address)
        return self.predictor.get(sig, self.default_prediction)

    def _train(self, pc: Optional[int], address: int, observed_distance: float) -> None:
        sig = self._signature(pc, address)
        old = self.predictor.get(sig, self.default_prediction)
        new = self.alpha * observed_distance + (1.0 - self.alpha) * old
        self.predictor[sig] = new

    def on_hit(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        line = cache_set.lines[line_index]
        if line.last_access_time is not None:
            observed_reuse = max(1, time_step - line.last_access_time)
            self._train(pc if pc is not None else line.owner_pc, address, float(observed_reuse))
        line.predicted_reuse = self._predict(pc, address)
        line.last_access_time = time_step
        line.owner_pc = pc
        self._update_recency(cache_set, line_index)

    def choose_victim(self, cache_set: CacheSet, address: int, pc: Optional[int], time_step: int) -> int:
        for idx, line in enumerate(cache_set.lines):
            if not line.valid:
                return idx

        # Escolhe a linha com maior reuso previsto. Em empate, usa maior LRU.
        return max(
            range(len(cache_set.lines)),
            key=lambda i: (cache_set.lines[i].predicted_reuse, cache_set.lines[i].lru),
        )

    def on_insert(self, cache_set: CacheSet, line_index: int, address: int, pc: Optional[int], time_step: int) -> None:
        line = cache_set.lines[line_index]
        line.predicted_reuse = self._predict(pc, address)
        line.last_access_time = time_step
        line.owner_pc = pc
        self._update_recency(cache_set, line_index)

    @staticmethod
    def _update_recency(cache_set: CacheSet, accessed_index: int) -> None:
        for idx, line in enumerate(cache_set.lines):
            if not line.valid:
                continue
            if idx == accessed_index:
                line.lru = 0
            else:
                line.lru += 1


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


def generate_random_trace(num_accesses: int, max_address: int, with_pc: bool = False) -> List[Dict[str, int]]:
    trace = []
    for _ in range(num_accesses):
        item = {"address": random.randrange(0, max_address, 4)}
        if with_pc:
            item["pc"] = random.choice([100, 104, 108, 112, 116])
        trace.append(item)
    return trace


def generate_streaming_trace(num_accesses: int, stride: int = 32, with_pc: bool = False) -> List[Dict[str, int]]:
    trace = []
    address = 0
    for _ in range(num_accesses):
        item = {"address": address}
        if with_pc:
            item["pc"] = 200
        trace.append(item)
        address += stride
    return trace


def generate_hotset_trace(num_accesses: int, hot_addresses: Optional[List[int]] = None, with_pc: bool = False) -> List[Dict[str, int]]:
    if hot_addresses is None:
        hot_addresses = [64, 96, 128, 160]
    trace = []
    for _ in range(num_accesses):
        item = {"address": random.choice(hot_addresses)}
        if with_pc:
            item["pc"] = 300
        trace.append(item)
    return trace


def generate_mixed_trace(num_accesses: int, stride: int = 32, with_pc: bool = False) -> List[Dict[str, int]]:
    trace = []
    stream_addr = 0
    hot_addresses = [64, 96, 128, 160]
    for i in range(num_accesses):
        if i % 5 == 0:
            item = {"address": random.choice(hot_addresses)}
            if with_pc:
                item["pc"] = 401
        else:
            item = {"address": stream_addr}
            if with_pc:
                item["pc"] = 400
            stream_addr += stride
        trace.append(item)
    return trace


def generate_matrix_trace(rows: int, cols: int, elem_size: int = 4, with_pc: bool = False) -> List[Dict[str, int]]:
    trace = []
    base = 0
    for r in range(rows):
        for c in range(cols):
            address = base + (r * cols + c) * elem_size
            item = {"address": address}
            if with_pc:
                item["pc"] = 500 + (r % 3)
            trace.append(item)
    return trace


def save_trace_csv(trace: List[Dict[str, int]], filename: str) -> None:
    fieldnames = sorted({k for item in trace for k in item.keys()})
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trace)


def load_trace_csv(filename: str) -> List[Dict[str, int]]:
    trace: List[Dict[str, int]] = []
    with open(filename, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            item: Dict[str, int] = {}
            if "address" not in row or row["address"] == "":
                raise ValueError("O CSV precisa ter a coluna 'address'.")
            item["address"] = int(row["address"])
            if "pc" in row and row["pc"] not in (None, ""):
                item["pc"] = int(row["pc"])
            trace.append(item)
    return trace


def build_policy(policy_name: str) -> ReplacementPolicy:
    normalized = policy_name.strip().lower()
    if normalized == "lru":
        return LRUPolicy()
    if normalized in {"mockingjay", "mockingjay_lite", "mj"}:
        return MockingjayLitePolicy()
    raise ValueError(f"Política desconhecida: {policy_name}")


def run_single(args: argparse.Namespace) -> Dict[str, float]:
    policy = build_policy(args.policy)
    simulator = CacheSimulator(
        cache_size=args.cache_size,
        block_size=args.block_size,
        associativity=args.associativity,
        policy=policy,
    )

    if args.trace_csv:
        trace = load_trace_csv(args.trace_csv)
    else:
        if args.trace_type == "random":
            trace = generate_random_trace(args.num_accesses, args.max_address, args.with_pc)
        elif args.trace_type == "streaming":
            trace = generate_streaming_trace(args.num_accesses, args.stride, args.with_pc)
        elif args.trace_type == "hotset":
            trace = generate_hotset_trace(args.num_accesses, with_pc=args.with_pc)
        elif args.trace_type == "mixed":
            trace = generate_mixed_trace(args.num_accesses, args.stride, args.with_pc)
        elif args.trace_type == "matrix":
            trace = generate_matrix_trace(args.matrix_rows, args.matrix_cols, with_pc=args.with_pc)
        else:
            raise ValueError("Tipo de traço inválido.")

    if args.save_trace:
        save_trace_csv(trace, args.save_trace)

    return simulator.run_trace(trace)


def compare_policies(args: argparse.Namespace) -> List[Dict[str, float]]:
    results = []
    for policy_name in ["lru", "mockingjay_lite"]:
        local_args = argparse.Namespace(**vars(args))
        local_args.policy = policy_name
        results.append(run_single(local_args))
    return results


def print_results(results: List[Dict[str, float]]) -> None:
    print("\n=== RESULTADOS ===")
    for result in results:
        print(f"Política: {result['policy']}")
        print(
            f"Cache={result['cache_size']} B | Bloco={result['block_size']} B | "
            f"Assoc={result['associativity']} | Conjuntos={result['num_sets']}"
        )
        print(
            f"Acessos={result['total_accesses']} | Hits={result['hits']} | Misses={result['misses']} | "
            f"Hit Rate={result['hit_rate']:.2f}% | Miss Rate={result['miss_rate']:.2f}%"
        )
        print("-" * 60)

    if len(results) == 2:
        gain = results[1]["hit_rate"] - results[0]["hit_rate"]
        print(f"Ganho de hit rate da segunda política em relação à primeira: {gain:+.2f} pontos percentuais")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Simulador de cache parametrizável com LRU e Mockingjay simplificado.")
    parser.add_argument("--cache-size", type=int, default=4096, help="Capacidade total da cache em bytes.")
    parser.add_argument("--block-size", type=int, default=32, help="Tamanho do bloco em bytes.")
    parser.add_argument("--associativity", type=int, default=2, help="Associatividade da cache.")
    parser.add_argument("--policy", type=str, default="lru", help="Política: lru ou mockingjay_lite.")
    parser.add_argument("--compare", action="store_true", help="Executa LRU e Mockingjay Lite no mesmo traço.")
    parser.add_argument("--trace-type", type=str, default="random", choices=["random", "streaming", "hotset", "mixed", "matrix"], help="Tipo de traço gerado.")
    parser.add_argument("--num-accesses", type=int, default=200, help="Número de acessos para traços gerados automaticamente.")
    parser.add_argument("--max-address", type=int, default=65536, help="Endereço máximo para traço aleatório.")
    parser.add_argument("--stride", type=int, default=32, help="Salto do traço sequencial/misto.")
    parser.add_argument("--matrix-rows", type=int, default=32, help="Número de linhas do traço matricial.")
    parser.add_argument("--matrix-cols", type=int, default=32, help="Número de colunas do traço matricial.")
    parser.add_argument("--trace-csv", type=str, default=None, help="Arquivo CSV de entrada com colunas address e opcionalmente pc.")
    parser.add_argument("--save-trace", type=str, default=None, help="Salva o traço gerado em CSV.")
    parser.add_argument("--with-pc", action="store_true", help="Gera traços com coluna PC sintética.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.compare:
        results = compare_policies(args)
    else:
        results = [run_single(args)]

    print_results(results)


if __name__ == "__main__":
    main()
