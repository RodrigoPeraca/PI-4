Como executar o projeto em Python

Este projeto simula o comportamento de uma memória cache e compara duas políticas de substituição: LRU e Mockingjay Lite.

1. Pré-requisitos

Antes de executar, é necessário ter instalado:

Python 3.10 ou superior

2. Instalação das dependências

### pip install -r requirements.txt

3. Estrutura esperada

O projeto deve estar organizado com os arquivos principais e a pasta traces, onde ficam os arquivos .csv usados na simulação.

Exemplo:

cache_simulator/
├── cli.py
├── simulator.py
├── io_utils.py
├── plot_results.py
├── traces/
│   ├── trace_random.csv
│   ├── trace_streaming.csv
│   ├── trace_hotset.csv
│   ├── trace_matrix.csv
│   ├── trace_mixed.csv
│   ├── trace_linked_list.csv
│   ├── trace_pattern_search.csv
│   └── trace_exemplo.csv
└── policies/

4. Executando a simulação

Para rodar o simulador, use:

### python cli.py

Ao executar, o programa exibirá no terminal a lista de traces disponíveis.
Basta escolher o número correspondente ao trace desejado.

Depois disso, o simulador executará automaticamente a comparação entre as políticas LRU e Mockingjay Lite, mostrando métricas como:

número total de acessos
hits
misses
hit rate
miss rate

5. Executando um trace específico

Se quiser rodar diretamente um arquivo CSV sem passar pelo menu interativo, use:

python cli.py --trace-csv traces/trace_random.csv

6. Alterando parâmetros da cache

Também é possível alterar os parâmetros da cache pela linha de comando. Exemplo:

python cli.py --trace-csv traces/trace_random.csv --cache-size 4096 --block-size 32 --associativity 2

7. Gerando gráficos comparativos

Para gerar gráficos comparando as políticas em todos os traces, execute:

### python plot_results.py

Os gráficos serão salvos automaticamente em uma pasta chamada plots/.