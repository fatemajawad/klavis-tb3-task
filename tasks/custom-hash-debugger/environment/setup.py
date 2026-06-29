from setuptools import setup, Extension

module = Extension(
    'fasthash',
    sources=['src/fasthash.c'],
    extra_compile_args=['-O2', '-Wall'],
)

setup(
    name='fasthash',
    version='1.0',
    ext_modules=[module],
)
