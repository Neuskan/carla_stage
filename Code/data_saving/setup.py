# cython:language_level=3

from setuptools import setup
from setuptools import Extension
from Cython.Distutils import build_ext

ext_modules = [
    Extension("data_saving",  ["data_saving.pyx"]),
]

setup(
    name = 'my_module',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules
)

for e in ext_modules:
    e.cython_directives = {'language_level': "3"}

