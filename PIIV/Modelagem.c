#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <ctype.h>

#define TAM_BLOCO 32
#define NUM_CONJUNTOS_L1 16
#define NUM_CONJUNTOS_L2 64
#define ASSOC_L1 2
#define ASSOC_L2 4
#define DEFAULT_NUM_ACESSOS 9000
#define MAX_ACESSOS 10000
#define MAX_ENDERECO 131072 // suficiente para suportar traces maiores
#define HISTORICO_MAX 10

#define POLITICA_LRU 0
#define POLITICA_MOCKINGJAAY 1

#define MAX_CONJUNTOS 128
#define MAX_ASSOC 4

typedef struct {
    int valido;
    int tag;
    int lru;
    int ultimo_acesso;
    int historico_intervalos[HISTORICO_MAX];
    int num_historico;
} Bloco;

typedef struct {
    Bloco blocos[MAX_ASSOC];
} Conjunto;

typedef struct {
    Conjunto conjuntos[MAX_CONJUNTOS];
    int num_conjuntos;
    int associatividade;
} Cache;

void inicializar_cache(Cache *cache, int num_conjuntos, int associatividade) {
    cache->num_conjuntos = num_conjuntos;
    cache->associatividade = associatividade;

    for (int i = 0; i < num_conjuntos; i++) {
        for (int j = 0; j < associatividade; j++) {
            cache->conjuntos[i].blocos[j].valido = 0;
            cache->conjuntos[i].blocos[j].tag = -1;
            cache->conjuntos[i].blocos[j].lru = 0;
            cache->conjuntos[i].blocos[j].ultimo_acesso = 0;
            cache->conjuntos[i].blocos[j].num_historico = 0;
        }
    }
}

void atualizar_lru(Conjunto *c, int associatividade, int acessado) {
    for (int i = 0; i < associatividade; i++) {
        if (!c->blocos[i].valido) {
            continue;
        }

        if (i == acessado) {
            c->blocos[i].lru = 0;
        } else {
            c->blocos[i].lru++;
        }
    }
}

int escolher_vitima(Conjunto *c, int associatividade) {
    for (int i = 0; i < associatividade; i++) {
        if (!c->blocos[i].valido) {
            return i;
        }
    }

    int indice = 0;
    int max = c->blocos[0].lru;

    for (int i = 1; i < associatividade; i++) {
        if (c->blocos[i].lru > max) {
            max = c->blocos[i].lru;
            indice = i;
        }
    }

    return indice;
}

int calcular_intervalo_estimado(Bloco *bloco, int tempo_atual) {
    if (bloco->num_historico == 0) {
        return tempo_atual - bloco->ultimo_acesso + 1;
    }

    int soma = 0;
    for (int i = 0; i < bloco->num_historico; i++) {
        soma += bloco->historico_intervalos[i];
    }
    int media = soma / bloco->num_historico;
    return media > 0 ? media : 1;
}

void atualizar_historico_mockingjaay(Bloco *bloco, int intervalo) {
    if (bloco->num_historico < HISTORICO_MAX) {
        bloco->historico_intervalos[bloco->num_historico] = intervalo;
        bloco->num_historico++;
    } else {
        for (int i = 0; i < HISTORICO_MAX - 1; i++) {
            bloco->historico_intervalos[i] = bloco->historico_intervalos[i + 1];
        }
        bloco->historico_intervalos[HISTORICO_MAX - 1] = intervalo;
    }
}

int escolher_vitima_mockingjaay(Conjunto *c, int associatividade, int tempo_atual) {
    for (int i = 0; i < associatividade; i++) {
        if (!c->blocos[i].valido) {
            return i;
        }
    }

    int indice = 0;
    int max_intervalo = calcular_intervalo_estimado(&c->blocos[0], tempo_atual);

    for (int i = 1; i < associatividade; i++) {
        int intervalo = calcular_intervalo_estimado(&c->blocos[i], tempo_atual);
        if (intervalo > max_intervalo) {
            max_intervalo = intervalo;
            indice = i;
        }
    }

    return indice;
}

void gerar_acessos(int acessos[], int numAcessos) {
    for (int i = 0; i < numAcessos; i++) {
        acessos[i] = rand() % MAX_ENDERECO;
    }
}

int ler_acessos_csv(const char *caminho, int acessos[], int *numAcessos) {
    FILE *arquivo = fopen(caminho, "r");
    if (!arquivo) {
        return 0;
    }

    char linha[256];
    *numAcessos = 0;

    if (fgets(linha, sizeof(linha), arquivo) == NULL) {
        fclose(arquivo);
        return 0;
    }

    while (fgets(linha, sizeof(linha), arquivo) != NULL && *numAcessos < MAX_ACESSOS) {
        char *linhaTrim = linha;
        while (isspace((unsigned char)*linhaTrim)) {
            linhaTrim++;
        }

        if (*linhaTrim == '\0' || *linhaTrim == '\n' || *linhaTrim == '#') {
            continue;
        }

        int endereco;
        if (sscanf(linhaTrim, "%d", &endereco) == 1) {
            acessos[(*numAcessos)++] = endereco;
            continue;
        }

        char *token = strtok(linhaTrim, ",");
        if (token != NULL && sscanf(token, "%d", &endereco) == 1) {
            acessos[(*numAcessos)++] = endereco;
        }
    }

    fclose(arquivo);
    return *numAcessos > 0;
}

int acessar_cache(Cache *cache, int endereco, int politica, int tempo_global) {
    int indice = (endereco / TAM_BLOCO) % cache->num_conjuntos;
    int tag = endereco / (TAM_BLOCO * cache->num_conjuntos);
    Conjunto *c = &cache->conjuntos[indice];

    for (int i = 0; i < cache->associatividade; i++) {
        if (c->blocos[i].valido && c->blocos[i].tag == tag) {
            if (politica == POLITICA_LRU) {
                atualizar_lru(c, cache->associatividade, i);
            } else {
                int intervalo = tempo_global - c->blocos[i].ultimo_acesso;
                atualizar_historico_mockingjaay(&c->blocos[i], intervalo);
                c->blocos[i].ultimo_acesso = tempo_global;
            }
            return 1;
        }
    }

    int vitima;
    if (politica == POLITICA_LRU) {
        vitima = escolher_vitima(c, cache->associatividade);
    } else {
        vitima = escolher_vitima_mockingjaay(c, cache->associatividade, tempo_global);
    }

    if (c->blocos[vitima].valido && politica == POLITICA_MOCKINGJAAY) {
        int intervalo = tempo_global - c->blocos[vitima].ultimo_acesso;
        atualizar_historico_mockingjaay(&c->blocos[vitima], intervalo);
    }

    c->blocos[vitima].valido = 1;
    c->blocos[vitima].tag = tag;
    c->blocos[vitima].ultimo_acesso = tempo_global;

    if (politica == POLITICA_LRU) {
        atualizar_lru(c, cache->associatividade, vitima);
    }

    return 0;
}

void preencher_cache(Cache *cache, int endereco, int politica, int tempo_global) {
    int indice = (endereco / TAM_BLOCO) % cache->num_conjuntos;
    int tag = endereco / (TAM_BLOCO * cache->num_conjuntos);
    Conjunto *c = &cache->conjuntos[indice];

    for (int i = 0; i < cache->associatividade; i++) {
        if (c->blocos[i].valido && c->blocos[i].tag == tag) {
            if (politica == POLITICA_LRU) {
                atualizar_lru(c, cache->associatividade, i);
            } else {
                int intervalo = tempo_global - c->blocos[i].ultimo_acesso;
                atualizar_historico_mockingjaay(&c->blocos[i], intervalo);
                c->blocos[i].ultimo_acesso = tempo_global;
            }
            return;
        }
    }

    int vitima;
    if (politica == POLITICA_LRU) {
        vitima = escolher_vitima(c, cache->associatividade);
    } else {
        vitima = escolher_vitima_mockingjaay(c, cache->associatividade, tempo_global);
    }

    if (c->blocos[vitima].valido && politica == POLITICA_MOCKINGJAAY) {
        int intervalo = tempo_global - c->blocos[vitima].ultimo_acesso;
        atualizar_historico_mockingjaay(&c->blocos[vitima], intervalo);
    }

    c->blocos[vitima].valido = 1;
    c->blocos[vitima].tag = tag;
    c->blocos[vitima].ultimo_acesso = tempo_global;

    if (politica == POLITICA_LRU) {
        atualizar_lru(c, cache->associatividade, vitima);
    }
}

static void imprimir_uso(const char *nome_programa) {
    printf("Uso: %s [trace.csv]\n", nome_programa);
    printf("Se nenhum arquivo for passado, o simulador gera acessos aleatórios.\n");
}

int main(int argc, char *argv[]) {
    int acessos[MAX_ACESSOS];
    int num_acessos = 0;

    if (argc > 2) {
        imprimir_uso(argv[0]);
        return 1;
    }

    if (argc == 2) {
        if (!ler_acessos_csv(argv[1], acessos, &num_acessos)) {
            fprintf(stderr, "Erro ao ler o arquivo CSV: %s\n", argv[1]);
            return 1;
        }
    } else {
        num_acessos = DEFAULT_NUM_ACESSOS;
        srand((unsigned) time(NULL));
        gerar_acessos(acessos, num_acessos);
    }

    printf("Acessos lidos: %d\n", num_acessos);
    for (int i = 0; i < num_acessos; i++) {
        printf("%d ", acessos[i]);
    }
    printf("\n\n");

    int politicas[2] = { POLITICA_LRU, POLITICA_MOCKINGJAAY };
    const char *nomes_politica[2] = { "LRU", "MockingJay" };

    for (int p = 0; p < 2; p++) {
        int politica = politicas[p];
        int tempo_global = 0;

        Cache cache_l1;
        Cache cache_l2;
        inicializar_cache(&cache_l1, NUM_CONJUNTOS_L1, ASSOC_L1);
        inicializar_cache(&cache_l2, NUM_CONJUNTOS_L2, ASSOC_L2);

        int hits_l1 = 0;
        int misses_l1 = 0;
        int hits_l2 = 0;
        int misses_l2 = 0;
        int mem_accesses = 0;

        for (int i = 0; i < num_acessos; i++) {
            int endereco = acessos[i];

            if (acessar_cache(&cache_l1, endereco, politica, tempo_global)) {
                hits_l1++;
            } else {
                misses_l1++;
                if (acessar_cache(&cache_l2, endereco, politica, tempo_global)) {
                    hits_l2++;
                    preencher_cache(&cache_l1, endereco, politica, tempo_global);
                } else {
                    misses_l2++;
                    preencher_cache(&cache_l2, endereco, politica, tempo_global);
                    preencher_cache(&cache_l1, endereco, politica, tempo_global);
                    mem_accesses++;
                }
            }

            tempo_global++;
        }

        printf("========== RESULTADO %s =========\n", nomes_politica[p]);
        printf("Total de acessos: %d\n", num_acessos);
        printf("L1 hits: %d\n", hits_l1);
        printf("L1 misses: %d\n", misses_l1);
        printf("L1 taxa de hit: %.2f%%\n\n", (100.0 * hits_l1) / num_acessos);

        printf("L2 hits: %d\n", hits_l2);
        printf("L2 misses: %d\n", misses_l2);
        if (misses_l1 > 0) {
            printf("L2 taxa de hit sobre misses L1: %.2f%%\n\n", (100.0 * hits_l2) / misses_l1);
        } else {
            printf("L2 taxa de hit sobre misses L1: N/A\n\n");
        }

        printf("Acessos à memória principal: %d\n", mem_accesses);
        printf("Taxa de acesso à memória principal: %.2f%%\n\n", (100.0 * mem_accesses) / num_acessos);
    }

    return 0;
}