/*
 * fastHash64 - Custom 64-bit hash function for data pipeline row ID generation.
 * Used to generate deterministic row identifiers in the ETL pipeline.
 *
 * Based on a modified MurmurHash3 finalizer with custom mixing constants.
 * BUG: One bit-shift direction is wrong, causing incorrect hash outputs.
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <string.h>

static uint64_t fastHash64(const void* key, int len, uint64_t seed) {
    const uint8_t* data = (const uint8_t*)key;
    const int nblocks = len / 8;
    uint64_t h = seed ^ (uint64_t)len;

    const uint64_t c1 = 0x87c37b91114253d5ULL;
    const uint64_t c2 = 0x4cf5ad432745937fULL;

    // Body
    const uint64_t* blocks = (const uint64_t*)data;
    for (int i = 0; i < nblocks; i++) {
        uint64_t k = blocks[i];
        k *= c1;
        // BUG: should be left shift (<<) not right shift (>>)
        k = (k >> 31) | (k << (64 - 31));  // rotl64(k, 31) -- BUG: >> should be <<
        k *= c2;
        h ^= k;
        h = (h << 27) | (h >> (64 - 27));  // rotl64(h, 27) -- correct
        h = h * 5 + 0x52dce729;
    }

    // Tail
    const uint8_t* tail = data + nblocks * 8;
    uint64_t k1 = 0;
    switch (len & 7) {
        case 7: k1 ^= (uint64_t)tail[6] << 48;
        case 6: k1 ^= (uint64_t)tail[5] << 40;
        case 5: k1 ^= (uint64_t)tail[4] << 32;
        case 4: k1 ^= (uint64_t)tail[3] << 24;
        case 3: k1 ^= (uint64_t)tail[2] << 16;
        case 2: k1 ^= (uint64_t)tail[1] << 8;
        case 1: k1 ^= (uint64_t)tail[0];
            k1 *= c1;
            k1 = (k1 << 31) | (k1 >> (64 - 31));  // correct
            k1 *= c2;
            h ^= k1;
    }

    // Finalization
    h ^= (uint64_t)len;
    h ^= h >> 33;
    h *= 0xff51afd7ed558ccdULL;
    h ^= h >> 33;
    h *= 0xc4ceb9fe1a85ec53ULL;
    h ^= h >> 33;

    return h;
}

static PyObject* py_hash_string(PyObject* self, PyObject* args) {
    const char* s;
    Py_ssize_t len;
    unsigned long long seed;

    if (!PyArg_ParseTuple(args, "s#K", &s, &len, &seed)) {
        return NULL;
    }

    uint64_t result = fastHash64(s, (int)len, (uint64_t)seed);
    return PyLong_FromUnsignedLongLong(result);
}

static PyObject* py_hash_bytes(PyObject* self, PyObject* args) {
    const char* data;
    Py_ssize_t len;
    unsigned long long seed;

    if (!PyArg_ParseTuple(args, "y#K", &data, &len, &seed)) {
        return NULL;
    }

    uint64_t result = fastHash64(data, (int)len, (uint64_t)seed);
    return PyLong_FromUnsignedLongLong(result);
}

static PyMethodDef HashMethods[] = {
    {"hash_string", py_hash_string, METH_VARARGS, "Hash a string with seed"},
    {"hash_bytes",  py_hash_bytes,  METH_VARARGS, "Hash bytes with seed"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef hashmodule = {
    PyModuleDef_HEAD_INIT, "fasthash", NULL, -1, HashMethods
};

PyMODINIT_FUNC PyInit_fasthash(void) {
    return PyModule_Create(&hashmodule);
}
