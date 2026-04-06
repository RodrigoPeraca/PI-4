#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define TAM_BLOCO 32
#define NUM_CONJUNTOS 8
#define ASSOC 2
#define NUM_ACESSOS 50
#define MAX_ENDERECO (TAM_BLOCO * NUM_CONJUNTOS * 8)

typedef struct {
    int valido;
    int tag;
    int lru; // contador para política LRU
} Bloco;

typedef struct {
    Bloco blocos[ASSOC];
} Conjunto;

typedef struct {
    Conjunto conjuntos[NUM_CONJUNTOS];
} Cache;

void inicializar_cache(Cache *cache) {
    for (int i = 0; i < NUM_CONJUNTOS; i++) {
        for (int j = 0; j < ASSOC; j++) {
            cache->conjuntos[i].blocos[j].valido = 0;
            cache->conjuntos[i].blocos[j].tag = -1;
            cache->conjuntos[i].blocos[j].lru = 0;
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
// Gerar acessos aleatórios
// =====================

void gerar_acessos(int acessos[], int numAcessos) {
    for (int i = 0; i < numAcessos; i++) {
        acessos[i] = rand() % MAX_ENDERECO;
    }
}

// =====================
// Acesso à cache
// =====================

int acessar_cache(Cache *cache, int endereco) {
    int indice = (endereco / TAM_BLOCO) % NUM_CONJUNTOS;
    int tag = endereco / (TAM_BLOCO * NUM_CONJUNTOS);

    Conjunto *c = &cache->conjuntos[indice];

    // Verificar HIT
    for (int i = 0; i < ASSOC; i++) {
        if (c->blocos[i].valido && c->blocos[i].tag == tag) {
            atualizar_lru(c, i);
            return 1; // HIT
        }
    }

    // MISS → substituir
    int vitima = escolher_vitima(c);

    c->blocos[vitima].valido = 1;
    c->blocos[vitima].tag = tag;

    atualizar_lru(c, vitima);

    return 0; // MISS
}

// =====================
// Função principal
// =====================

int main() {
    Cache cache;
    inicializar_cache(&cache);

    int acessos[NUM_ACESSOS];
    srand((unsigned) time(NULL));
    gerar_acessos(acessos, NUM_ACESSOS);

    int hits = 0;
    int misses = 0;

    printf("Acessos gerados:\n");
    for (int i = 0; i < NUM_ACESSOS; i++) {
        printf("%d ", acessos[i]);
    }
    printf("\n\n");

    for (int i = 0; i < NUM_ACESSOS; i++) {
        if (acessar_cache(&cache, acessos[i])) {
            printf("Endereco %d -> HIT\n", acessos[i]);
            hits++;
        } else {
            printf("Endereco %d -> MISS\n", acessos[i]);
            misses++;
        }
    }

    printf("\nResumo:\n");
    printf("Hits: %d\n", hits);
    printf("Misses: %d\n", misses);

    return 0;
}