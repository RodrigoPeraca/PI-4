import csv
import random
from pathlib import Path

TRACES_DIR = Path(__file__).parent / "generators"

NUM_ACCESSES = 2000
MAX_ADDRESS = 32768
WORD_SIZE = 4
BLOCK_SIZE = 32

random.seed(42)


def aligned_address(max_address=MAX_ADDRESS, align=WORD_SIZE):
    return random.randrange(0, max_address, align)


def save_trace_csv(filename, trace):
    if not trace:
        raise ValueError(f"Trace vazio: {filename}")

    fieldnames = list(trace[0].keys())
    path = TRACES_DIR / filename

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trace)


def generate_random_trace():
    trace = []
    pcs = [100, 104, 108, 112, 116]

    for _ in range(NUM_ACCESSES):
        trace.append({
            "address": aligned_address(),
            "pc": random.choice(pcs)
        })

    return trace


def generate_streaming_trace():
    trace = []
    address = 0
    pc = 200

    for _ in range(NUM_ACCESSES):
        trace.append({
            "address": address % MAX_ADDRESS,
            "pc": pc
        })
        address += BLOCK_SIZE

    return trace


def generate_hotset_trace():
    trace = []
    hot_addresses = [64, 96, 128, 160, 192, 224]
    pcs = [300, 304]

    for _ in range(NUM_ACCESSES):
        if random.random() < 0.8:
            addr = random.choice(hot_addresses)
        else:
            addr = aligned_address()

        trace.append({
            "address": addr,
            "pc": random.choice(pcs)
        })

    return trace


def generate_matrix_trace():
    trace = []
    rows = 40
    cols = 50
    elem_size = 4
    base = 0

    for i in range(NUM_ACCESSES):
        r = i // cols
        c = i % cols
        address = base + (r * cols + c) * elem_size
        address %= MAX_ADDRESS

        trace.append({
            "address": address,
            "pc": 500 + (r % 4)
        })

    return trace


def generate_mixed_trace():
    trace = []
    stream_addr = 0
    hot_addresses = [64, 96, 128, 160]
    pcs_stream = [400, 404]
    pcs_hot = [410, 414]
    pcs_random = [420, 424]

    for i in range(NUM_ACCESSES):
        mode = i % 10

        if mode in [0, 1]:
            trace.append({
                "address": random.choice(hot_addresses),
                "pc": random.choice(pcs_hot)
            })
        elif mode in [2, 3, 4, 5, 6]:
            trace.append({
                "address": stream_addr % MAX_ADDRESS,
                "pc": random.choice(pcs_stream)
            })
            stream_addr += BLOCK_SIZE
        else:
            trace.append({
                "address": aligned_address(),
                "pc": random.choice(pcs_random)
            })

    return trace


def generate_linked_list_trace():
    trace = []
    pcs = [600, 604]

    nodes = random.sample(range(0, MAX_ADDRESS, BLOCK_SIZE), 256)
    current = random.choice(nodes)

    for _ in range(NUM_ACCESSES):
        trace.append({
            "address": current,
            "pc": random.choice(pcs)
        })

        if random.random() < 0.7:
            current = random.choice(nodes)
        else:
            current = aligned_address(align=BLOCK_SIZE)

    return trace


def generate_pattern_search_trace():
    trace = []
    pcs = [700, 704, 708]
    base_regions = [2048, 4096, 8192, 12288]

    for i in range(NUM_ACCESSES):
        region = base_regions[(i // 200) % len(base_regions)]

        if i % 20 < 14:
            offset = (i % 16) * WORD_SIZE
        else:
            offset = random.randrange(0, 512, WORD_SIZE)

        trace.append({
            "address": (region + offset) % MAX_ADDRESS,
            "pc": random.choice(pcs)
        })

    return trace


def generate_example_trace():
    trace = []
    pcs = [800, 804]

    pattern = [0, 32, 64, 96, 0, 32, 128, 160, 0, 32]

    for i in range(NUM_ACCESSES):
        trace.append({
            "address": pattern[i % len(pattern)],
            "pc": random.choice(pcs)
        })

    return trace


def main():
    TRACES_DIR.mkdir(exist_ok=True)

    traces = {
        "trace_random.csv": generate_random_trace(),
        "trace_streaming.csv": generate_streaming_trace(),
        "trace_hotset.csv": generate_hotset_trace(),
        "trace_matrix.csv": generate_matrix_trace(),
        "trace_mixed.csv": generate_mixed_trace(),
        "trace_linked_list.csv": generate_linked_list_trace(),
        "trace_pattern_search.csv": generate_pattern_search_trace(),
        "trace_exemplo.csv": generate_example_trace(),
    }

    for filename, trace in traces.items():
        save_trace_csv(filename, trace)
        print(f"[OK] {filename} gerado com {len(trace)} acessos")

    print("\nTodos os traces foram gerados com sucesso.")


if __name__ == "__main__":
    main()