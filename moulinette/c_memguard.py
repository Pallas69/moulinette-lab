"""Harnais C de protection mémoire par pages de garde (mmap / mprotect).

Fournit :
- un allocateur malloc/free adossé à une page de garde PROT_NONE en fin de bloc
  (détectant au premier octet tout débordement de tampon), un remplissage poison
  0xA5 (détectant l'oubli d'initialisation ou de '\\0' final) et une mise en
  quarantaine PROT_NONE lors de free() (détectant les use-after-free et double-free) ;
- ml_ro_str() pour placer une chaîne d'entrée en page lecture seule (PROT_READ)
  juste avant une page PROT_NONE (détectant à la fois l'écriture sur une entrée
  constante et la lecture hors bornes) ;
- ml_unfreed_count() pour vérifier la libération effective des maillons alloués.
"""

MEMGUARD_C = r'''
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#ifndef MAP_ANONYMOUS
#define MAP_ANONYMOUS 0x20
#endif

typedef struct s_ml_alloc {
    void *ptr;
    unsigned char *base;
    size_t map_len;
    size_t size;
    int freed;
} t_ml_alloc;

static t_ml_alloc ml_allocs[2048];
static size_t ml_alloc_total = 0;
static size_t ml_alloc_live = 0;

void *malloc(size_t size)
{
    size_t pg = 4096;
    size_t alloc_sz = size == 0 ? 1 : size;
    size_t data_len = ((alloc_sz + pg - 1) / pg) * pg;
    size_t total_len = data_len + pg;
    unsigned char *base;
    void *user_ptr;

    if (total_len < data_len)
        return (0);
    base = (unsigned char *)mmap(0, total_len, PROT_READ | PROT_WRITE,
                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED)
        return (0);
    if (mprotect(base + data_len, pg, PROT_NONE) != 0)
    {
        munmap(base, total_len);
        return (0);
    }
    user_ptr = (void *)(base + (data_len - alloc_sz));
    memset(user_ptr, 0xA5, alloc_sz);
    if (ml_alloc_total < 2048)
    {
        ml_allocs[ml_alloc_total].ptr = user_ptr;
        ml_allocs[ml_alloc_total].base = base;
        ml_allocs[ml_alloc_total].map_len = total_len;
        ml_allocs[ml_alloc_total].size = size;
        ml_allocs[ml_alloc_total].freed = 0;
        ml_alloc_total++;
    }
    ml_alloc_live++;
    return (user_ptr);
}

void free(void *ptr)
{
    size_t i;

    if (!ptr)
        return ;
    for (i = 0; i < ml_alloc_total; i++)
    {
        if (ml_allocs[i].ptr == ptr)
        {
            if (ml_allocs[i].freed)
                _exit(86);
            ml_allocs[i].freed = 1;
            if (ml_alloc_live > 0)
                ml_alloc_live--;
            mprotect(ml_allocs[i].base, ml_allocs[i].map_len, PROT_NONE);
            return ;
        }
    }
    _exit(87);
}

__attribute__((unused))
static size_t ml_unfreed_count(void)
{
    return (ml_alloc_live);
}

__attribute__((unused))
static void *ml_guard_buf(const void *src, size_t n)
{
    size_t pg = 4096;
    size_t alloc_sz = n == 0 ? 1 : n;
    size_t data_len = ((alloc_sz + pg - 1) / pg) * pg;
    size_t total_len = data_len + pg;
    unsigned char *base;
    void *dst;

    base = (unsigned char *)mmap(0, total_len, PROT_READ | PROT_WRITE,
                                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (base == MAP_FAILED)
        _exit(88);
    if (mprotect(base + data_len, pg, PROT_NONE) != 0)
        _exit(88);
    dst = (void *)(base + (data_len - alloc_sz));
    if (n > 0 && src)
        memcpy(dst, src, n);
    return (dst);
}

__attribute__((unused))
static char *ml_ro_str(const char *s)
{
    size_t len = strlen(s) + 1;
    size_t pg = 4096;
    size_t data_len = ((len + pg - 1) / pg) * pg;
    char *dst = (char *)ml_guard_buf(s, len);
    unsigned char *base = (unsigned char *)dst - (data_len - len);

    if (mprotect(base, data_len, PROT_READ) != 0)
        _exit(88);
    return (dst);
}
'''
