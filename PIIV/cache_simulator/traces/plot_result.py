import os
from pathlib import Path
import matplotlib.pyplot as plt
import sys 

sys.path.append(str(Path(__file__).resolve().parent.parent))

from simulator import CacheSimulator
from policies.registry import build_policy
from io_utils import load_trace_csv

TRACES_DIR = Path(__file__).parent / "generators"
PLOTS_DIR = Path(__file__).parent / "plots"

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

CACHE_SIZE = 4096
BLOCK_SIZE = 32
ASSOCIATIVITY = 2


def run_single(policy_name: str, trace_path: Path) -> dict:
    policy = build_policy(policy_name)

    simulator = CacheSimulator(
        cache_size=CACHE_SIZE,
        block_size=BLOCK_SIZE,
        associativity=ASSOCIATIVITY,
        policy=policy,
    )

    trace = load_trace_csv(str(trace_path))
    return simulator.run_trace(trace)


def collect_results():
    results = []

    for trace_name, filename in AVAILABLE_TRACES.items():
        trace_path = TRACES_DIR / filename

        if not trace_path.exists():
            print(f"[AVISO] Trace não encontrado: {trace_path}")
            continue

        lru_result = run_single("lru", trace_path)
        mockingjay_result = run_single("mockingjay_lite", trace_path)

        results.append({
            "trace": trace_name,
            "lru_hit_rate": lru_result["hit_rate"],
            "mockingjay_hit_rate": mockingjay_result["hit_rate"],
            "lru_hits": lru_result["hits"],
            "mockingjay_hits": mockingjay_result["hits"],
            "lru_misses": lru_result["misses"],
            "mockingjay_misses": mockingjay_result["misses"],
        })

    return results


def plot_hit_rate_comparison(results):
    trace_names = [r["trace"] for r in results]
    lru_rates = [r["lru_hit_rate"] for r in results]
    mockingjay_rates = [r["mockingjay_hit_rate"] for r in results]

    x = range(len(trace_names))
    width = 0.35

    plt.figure(figsize=(12, 6))
    plt.bar([i - width / 2 for i in x], lru_rates, width=width, label="LRU")
    plt.bar([i + width / 2 for i in x], mockingjay_rates, width=width, label="Mockingjay Lite")

    plt.xticks(list(x), trace_names, rotation=30)
    plt.ylabel("Hit Rate (%)")
    plt.title("Comparação Geral de Hit Rate por Trace")
    plt.legend()
    plt.tight_layout()

    output_path = PLOTS_DIR / "comparacao_geral_hit_rate.png"
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[OK] Gráfico salvo em: {output_path}")


def plot_gain_comparison(results):
    trace_names = [r["trace"] for r in results]
    gains = [r["mockingjay_hit_rate"] - r["lru_hit_rate"] for r in results]

    x = range(len(trace_names))

    plt.figure(figsize=(12, 6))
    plt.bar(list(x), gains)

    plt.xticks(list(x), trace_names, rotation=30)
    plt.ylabel("Ganho de Hit Rate (p.p.)")
    plt.title("Ganho do Mockingjay Lite em relação ao LRU")
    plt.tight_layout()

    output_path = PLOTS_DIR / "ganho_mockingjay_vs_lru.png"
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[OK] Gráfico salvo em: {output_path}")


def plot_individual_trace_comparisons(results):
    for r in results:
        trace_name = r["trace"]
        labels = ["LRU", "Mockingjay Lite"]
        values = [r["lru_hit_rate"], r["mockingjay_hit_rate"]]

        plt.figure(figsize=(8, 5))
        plt.bar(labels, values)
        plt.ylabel("Hit Rate (%)")
        plt.title(f"Comparação de Hit Rate - Trace {trace_name}")
        plt.ylim(0, max(values) + 10 if max(values) > 0 else 10)
        plt.tight_layout()

        output_path = PLOTS_DIR / f"comparacao_{trace_name}.png"
        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"[OK] Gráfico individual salvo em: {output_path}")


def main():
    PLOTS_DIR.mkdir(exist_ok=True)

    results = collect_results()

    if not results:
        print("Nenhum resultado foi coletado.")
        return

    print("\n=== RESULTADOS COLETADOS ===")
    for r in results:
        print(
            f"{r['trace']}: "
            f"LRU={r['lru_hit_rate']:.2f}% | "
            f"Mockingjay={r['mockingjay_hit_rate']:.2f}%"
        )

    plot_hit_rate_comparison(results)
    plot_gain_comparison(results)
    plot_individual_trace_comparisons(results)


if __name__ == "__main__":
    main()