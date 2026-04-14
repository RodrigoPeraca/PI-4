#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define TAM_BLOCO 32
#define NUM_CONJUNTOS 32
#define ASSOC 2
#define NUM_ACESSOS 50
#define MAX_ENDERECO 32768 // 16x o tamanho total da cache (32 conjuntos x 2 vias x 32 bytes por bloco)
#define HISTORICO_MAX 10
#define POLITICA_LRU 0
#define POLITICA_MOCKINGJAAY 1

typedef struct {
    int valido;
    int tag;
    int lru;                          // contador para política LRU
    int ultimo_acesso;                 // timestamp do último acesso (MockingJay)
    int intervalo_estimado;            // intervalo estimado até próximo reuso
    int historico_intervalos[HISTORICO_MAX]; // histórico dos últimos intervalos
    int num_historico;                 // quantidade de intervalos no histórico
} Bloco;

typedef struct {
    Bloco blocos[ASSOC];
} Conjunto;

typedef struct {
    Conjunto conjuntos[NUM_CONJUNTOS];
    int tempo_global;                 // contador global de ciclos de acesso
} Cache;

void inicializar_cache(Cache *cache) {
    cache->tempo_global = 0;
    for (int i = 0; i < NUM_CONJUNTOS; i++) {
        for (int j = 0; j < ASSOC; j++) {
            cache->conjuntos[i].blocos[j].valido = 0;
            cache->conjuntos[i].blocos[j].tag = -1;
            cache->conjuntos[i].blocos[j].lru = 0;
            cache->conjuntos[i].blocos[j].ultimo_acesso = 0;
            cache->conjuntos[i].blocos[j].intervalo_estimado = 0;
            cache->conjuntos[i].blocos[j].num_historico = 0;
        }
    }
}

// =====================
// Atualizar LRU
// =====================

void atualizar_lru(Conjunto *c, int acessado) {
    for (int i = 0; i < ASSOC; i++) {
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

// =====================
// Escolher vítima (LRU)
// =====================

int escolher_vitima(Conjunto *c) {
    for (int i = 0; i < ASSOC; i++) {
        if (!c->blocos[i].valido) {
            return i;
        }
    }

    int indice = 0;
    int max = c->blocos[0].lru;

    for (int i = 1; i < ASSOC; i++) {
        if (c->blocos[i].lru > max) {
            max = c->blocos[i].lru;
            indice = i;
        }
    }

    return indice;
}

// =====================
// Calcular intervalo estimado (MockingJay)
// =====================

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

// =====================
// Atualizar histórico de intervalos (MockingJay)
// =====================

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

// =====================
// Escolher vítima (MockingJay)
// =====================

int escolher_vitima_mockingjaay(Conjunto *c, int tempo_atual) {
    for (int i = 0; i < ASSOC; i++) {
        if (!c->blocos[i].valido) {
            return i;
        }
    }

    int indice = 0;
    int max_intervalo = calcular_intervalo_estimado(&c->blocos[0], tempo_atual);

    for (int i = 1; i < ASSOC; i++) {
        int intervalo = calcular_intervalo_estimado(&c->blocos[i], tempo_atual);
        if (intervalo > max_intervalo) {
            max_intervalo = intervalo;
            indice = i;
        }
    }

    return indice;
}

// =====================
// Gerar acessos aleatórios
// =====================

void gerar_acessos(int acessos[], int numAcessos) {
    for (int i = 0; i < numAcessos; i++) {
        acessos[i] = rand() % MAX_ENDERECO;
    }
}

// =====================
// Acesso à cache com política selecionável
// =====================

int acessar_cache(Cache *cache, int endereco, int politica) {
    int indice = (endereco / TAM_BLOCO) % NUM_CONJUNTOS;
    int tag = endereco / (TAM_BLOCO * NUM_CONJUNTOS);

    Conjunto *c = &cache->conjuntos[indice];

    // Verificar HIT
    for (int i = 0; i < ASSOC; i++) {
        if (c->blocos[i].valido && c->blocos[i].tag == tag) {
            if (politica == POLITICA_LRU) {
                atualizar_lru(c, i);
            } else if (politica == POLITICA_MOCKINGJAAY) {
                int intervalo = cache->tempo_global - c->blocos[i].ultimo_acesso;
                atualizar_historico_mockingjaay(&c->blocos[i], intervalo);
                c->blocos[i].ultimo_acesso = cache->tempo_global;
            }
            cache->tempo_global++;
            return 1; // HIT
        }
    }

    // MISS → substituir
    int vitima;
    if (politica == POLITICA_LRU) {
        vitima = escolher_vitima(c);
    } else {
        vitima = escolher_vitima_mockingjaay(c, cache->tempo_global);
    }

    // Se tinha um bloco válido antes, atualizar histórico
    if (c->blocos[vitima].valido && politica == POLITICA_MOCKINGJAAY) {
        int intervalo = cache->tempo_global - c->blocos[vitima].ultimo_acesso;
        atualizar_historico_mockingjaay(&c->blocos[vitima], intervalo);
    }

    c->blocos[vitima].valido = 1;
    c->blocos[vitima].tag = tag;
    c->blocos[vitima].ultimo_acesso = cache->tempo_global;

    if (politica == POLITICA_LRU) {
        atualizar_lru(c, vitima);
    }

    cache->tempo_global++;
    return 0; // MISS
}

// =====================
// Função principal
// =====================

int main() {
    int acessos[NUM_ACESSOS];
    srand((unsigned) time(NULL));
    gerar_acessos(acessos, NUM_ACESSOS);

    printf("Acessos gerados:\n");
    for (int i = 0; i < NUM_ACESSOS; i++) {
        printf("%d ", acessos[i]);
    }
    printf("\n\n");

    // ===== Teste com LRU =====
    printf("========== POLITICA LRU ==========\n");
    Cache cache_lru;
    inicializar_cache(&cache_lru);

    int hits_lru = 0, misses_lru = 0;
    for (int i = 0; i < NUM_ACESSOS; i++) {
        if (acessar_cache(&cache_lru, acessos[i], POLITICA_LRU)) {
            hits_lru++;
        } else {
            misses_lru++;
        }
    }

    printf("\nResumo LRU:\n");
    printf("Hits:  %d\n", hits_lru);
    printf("Misses: %d\n", misses_lru);
    printf("Taxa de hit: %.2f%%\n\n", (100.0 * hits_lru) / NUM_ACESSOS);

    // ===== Teste com MockingJay =====
    printf("========== POLITICA MOCKINGJAAY ==========\n");
    Cache cache_mockingjaay;
    inicializar_cache(&cache_mockingjaay);

    int hits_mockingjaay = 0, misses_mockingjaay = 0;
    for (int i = 0; i < NUM_ACESSOS; i++) {
        if (acessar_cache(&cache_mockingjaay, acessos[i], POLITICA_MOCKINGJAAY)) {
            hits_mockingjaay++;
        } else {
            misses_mockingjaay++;
        }
    }

    printf("\nResumo MockingJay:\n");
    printf("Hits:  %d\n", hits_mockingjaay);
    printf("Misses: %d\n", misses_mockingjaay);
    printf("Taxa de hit: %.2f%%\n\n", (100.0 * hits_mockingjaay) / NUM_ACESSOS);

    // ===== Comparacao =====
    printf("========== COMPARACAO ==========\n");
    printf("LRU:         %d hits | %d misses\n", hits_lru, misses_lru);
    printf("MockingJay:  %d hits | %d misses\n", hits_mockingjaay, misses_mockingjaay);
    printf("Diferenca:   %d hits (MockingJay - LRU)\n", hits_mockingjaay - hits_lru);

    return 0;
}