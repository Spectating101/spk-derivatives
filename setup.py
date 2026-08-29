"""Legacy setuptools compatibility shim.

Canonical package metadata lives in ``pyproject.toml``. Keeping this file
minimal prevents version/description drift between two packaging authorities.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
