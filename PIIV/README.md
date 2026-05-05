# Simulador de Cache - Sprint 1

Este material foi preparado para a fase de modelagem da Sprint 1.
### IMPORTANTE: COMO RODAR O PROJETO ?

--> Projeto Python
### Ler o README que está dentro da pasta do cache_simulator

--> Projeto C
### Compilação
```bash
gcc Modelagem.c -o cache_simulator
```

### Execução
- Com arquivo CSV de traços:
```bash
./cache_simulator caminho/para/trace.csv
```
- Sem arquivo (gera acessos aleatórios):
```bash
./cache_simulator
```

## O que o código Modelagem.c faz
O arquivo `Modelagem.c` implementa um simulador de cache hierárquica em C, simulando caches L1 e L2 com duas políticas de substituição: LRU e MockingJay.

### Estruturas de Dados
- **Bloco**: Contém validade, tag, contador LRU, último acesso e histórico de intervalos (para MockingJay).
- **Conjunto**: Grupo de blocos com associatividade definida.
- **Cache**: Estrutura com conjuntos, número de conjuntos e associatividade.

### Políticas de Substituição
1. **LRU (Least Recently Used)**: Substitui o bloco menos recentemente usado, atualizando contadores a cada acesso.
2. **MockingJay**: Baseada em predição de reúso, mantém histórico de intervalos entre acessos para estimar reutilização futura.

### Hierarquia de Cache
- **L1**: 16 conjuntos, associatividade 2.
- **L2**: 64 conjuntos, associatividade 4.
- Simula inclusividade: Misses em L1 verificam L2, preenchendo ambas quando necessário.

### Entrada de Dados
- Lê acessos de um arquivo CSV (endereços decimais, um por linha ou separados por vírgula).
- Gera 9000 acessos aleatórios se nenhum arquivo for fornecido.

### Saída
Imprime estatísticas para cada política: hits/misses L1 e L2, taxas de hit e acessos à memória principal.

### Exemplo de Saída
```
========== RESULTADO LRU =========
Total de acessos: 9000
L1 hits: 4500
L1 misses: 4500
L1 taxa de hit: 50.00%

L2 hits: 2000
L2 misses: 2500
L2 taxa de hit sobre misses L1: 44.44%

Acessos à memória principal: 2500
Taxa de acesso à memória principal: 27.78%
```

### Constantes Principais
- TAM_BLOCO: 32 bytes
- NUM_CONJUNTOS_L1: 16
- ASSOC_L1: 2
- NUM_CONJUNTOS_L2: 64
- ASSOC_L2: 4
- DEFAULT_NUM_ACESSOS: 9000

Este simulador é útil para analisar desempenho de caches e comparar políticas de substituição.

## O que o código faz
- Simula uma cache parametrizável
- Permite testar as políticas `LRU` e `Mockingjay Lite`
- Permite gerar traços automáticos
- Permite ler traços a partir de um CSV
- Compara as duas políticas usando exatamente o mesmo traço

## Observação importante
A implementação `Mockingjay Lite` é uma versão simplificada inspirada no algoritmo Mockingjay. Ela é adequada para a Sprint 1 como modelagem inicial, mas não representa uma implementação fiel do paper original.

## Parâmetros principais
- `--cache-size`: capacidade da cache em bytes
- `--block-size`: tamanho do bloco em bytes
- `--associativity`: associatividade
- `--policy`: `lru` ou `mockingjay_lite`
- `--compare`: roda as duas políticas no mesmo traço
- `--trace-type`: `random`, `streaming`, `hotset`, `mixed`, `matrix`
- `--trace-csv`: lê um traço de um arquivo CSV
- `--save-trace`: salva um traço gerado em CSV
- `--with-pc`: gera um PC sintético no traço

## Exemplos de uso

### 1. Rodar apenas LRU
```bash
python simulator_cache.py --policy lru --trace-type mixed --num-accesses 200
```

### 2. Comparar LRU e Mockingjay Lite
```bash
python simulator_cache.py --compare --trace-type mixed --num-accesses 200
```

### 3. Testar uma cache diferente
```bash
python simulator_cache.py --compare --cache-size 8192 --block-size 32 --associativity 4 --trace-type hotset --num-accesses 500
```

### 4. Ler traço de CSV
```bash
python simulator_cache.py --compare --trace-csv trace_exemplo.csv
```

### 5. Gerar e salvar um traço
```bash
python simulator_cache.py --trace-type streaming --num-accesses 100 --save-trace trace_streaming.csv
```

## Formato do CSV
O CSV deve conter pelo menos a coluna `address`.
Pode conter também a coluna `pc`.

Exemplo:
```csv
address,pc
64,100
96,100
128,104
64,100
```

## 6 Explicação Trace type:
- Random

Representa acessos sem localidade clara.
É útil para teste básico, mas geralmente não é o mais realista.

- Streaming

Representa leitura sequencial de um grande vetor ou bloco de memória.
Isso é muito comum em programas numéricos, processamento de arrays e leitura contínua de dados.

- Hotset

Representa um pequeno conjunto de endereços que é acessado repetidamente.
Isso simula dados “quentes”, muito reutilizados.

- Mixed

Mistura streaming com hotset.
Esse tipo é muito útil porque simula situações em que parte da memória é percorrida continuamente, mas alguns dados específicos continuam sendo reutilizados.

- Matrix

Representa acesso a estruturas bidimensionais, como matrizes.
Isso também é muito comum em computação científica e benchmarks clássicos.

Então esses padrões não são “oficiais” como um pacote universal obrigatório, mas são padrões sintéticos clássicos e coerentes para estudar cache.