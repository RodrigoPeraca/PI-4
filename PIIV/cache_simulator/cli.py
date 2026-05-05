import argparse
from pathlib import Path

from simulator import CacheSimulator
from policies.registry import build_policy
from io_utils import load_trace_csv

TRACES_DIR = Path(__file__).parent / "traces\generators"

AVAILABLE_TRACES = {
    "random": "trace_random.csv",
    "streaming": "trace_streaming.csv",
    "hotset": "trace_hotset.csv",
    "matrix": "trace_matrix.csv",
    "mixed": "trace_mixed.csv",
    "linked_list": "trace_linked_list.csv",
    "pattern_search": "trace_pattern_search.csv",
    "exemplo": "trace_exemplo.csv",
}


def select_trace_interactively() -> Path:
    """Mostra um menu simples para o usuário escolher um trace CSV."""
    print("\n=== Traces disponíveis ===")
    options = list(AVAILABLE_TRACES.items())

    for i, (name, filename) in enumerate(options, start=1):
        trace_path = TRACES_DIR / filename
        status = "" if trace_path.exists() else " [não encontrado]"
        print(f"  [{i}] {name:<16} {filename}{status}")

    print()

    while True:
        raw = input("Escolha o número do trace (ou Enter para 'random'): ").strip()

        if raw == "":
            return TRACES_DIR / AVAILABLE_TRACES["random"]

        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(options):
                _, filename = options[index - 1]
                return TRACES_DIR / filename

        print(f"Opção inválida. Digite um número entre 1 e {len(options)}.")


def run_single(
    cache_size: int,
    block_size: int,
    associativity: int,
    policy_name: str,
    trace_path: Path,
) -> dict:
    """Executa uma única política sobre um trace."""
    policy = build_policy(policy_name)

    simulator = CacheSimulator(
        cache_size=cache_size,
        block_size=block_size,
        associativity=associativity,
        policy=policy,
    )

    trace = load_trace_csv(str(trace_path))
    return simulator.run_trace(trace)


def compare_policies(
    cache_size: int,
    block_size: int,
    associativity: int,
    trace_path: Path,
) -> list[dict]:
    """Executa LRU e Mockingjay Lite no mesmo trace."""
    results = []

    for policy_name in ["lru", "mockingjay_lite"]:
        result = run_single(
            cache_size=cache_size,
            block_size=block_size,
            associativity=associativity,
            policy_name=policy_name,
            trace_path=trace_path,
        )
        results.append(result)

    return results


def print_results(results: list[dict]) -> None:
    """Exibe os resultados no terminal."""
    print("\n=== RESULTADOS ===")

    for result in results:
        print(f"Política : {result['policy']}")
        print(
            f"Cache={result['cache_size']} B | "
            f"Bloco={result['block_size']} B | "
            f"Assoc={result['associativity']} | "
            f"Conjuntos={result['num_sets']}"
        )
        print(
            f"Acessos={result['total_accesses']} | "
            f"Hits={result['hits']} | "
            f"Misses={result['misses']} | "
            f"Hit Rate={result['hit_rate']:.2f}% | "
            f"Miss Rate={result['miss_rate']:.2f}%"
        )
        print("-" * 60)

    if len(results) == 2:
        gain = results[1]["hit_rate"] - results[0]["hit_rate"]
        print(f"Ganho Mockingjay vs LRU: {gain:+.2f} p.p.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulador de cache com seleção de trace CSV."
    )

    parser.add_argument(
        "--cache-size",
        type=int,
        default=4096,
        help="Capacidade total da cache em bytes.",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=32,
        help="Tamanho do bloco em bytes.",
    )
    parser.add_argument(
        "--associativity",
        type=int,
        default=2,
        help="Associatividade da cache.",
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="lru",
        help="Política de substituição: lru ou mockingjay_lite.",
    )
    parser.add_argument(
        "--trace-csv",
        type=str,
        default=None,
        help="Caminho direto para um CSV. Se omitido, abre o menu interativo.",
    )

    return parser


def resolve_trace_path(trace_csv_arg: str | None) -> Path:
    """Resolve o caminho do trace, via argumento ou menu interativo."""
    if trace_csv_arg:
        return Path(trace_csv_arg)

    return select_trace_interactively()


def main() -> None:
    args = build_parser().parse_args()
    
    while True:
        trace_path = resolve_trace_path(args.trace_csv)
        print(trace_path)
        
        if not trace_path.exists():
            raise FileNotFoundError(f"Trace não encontrado: {trace_path}")

        results = compare_policies(
            cache_size=args.cache_size,
            block_size=args.block_size,
            associativity=args.associativity,
            trace_path=trace_path,
        )

        print_results(results)


if __name__ == "__main__":
    main()