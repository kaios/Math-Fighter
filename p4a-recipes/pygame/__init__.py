"""python-for-android recipe override: newer pygame.

The stock recipe pins pygame 2.1.0, whose generated C code does not compile
against the Python 3.14 that python-for-android now ships. pygame 2.6.1's
source archive has no generated C, so setup.py runs Cython on the host;
Cython 3.1+ is needed for Python 3.14, and it rejects one line of
pygame's _sprite.pyx, which the patch removes.
"""
from pythonforandroid.recipes.pygame import Pygame2Recipe


class NewerPygameRecipe(Pygame2Recipe):
    version = '2.6.1'
    hostpython_prerequisites = ['setuptools', 'cython>=3.1']
    patches = ['cython31-sprite-dict.patch']


recipe = NewerPygameRecipe()
