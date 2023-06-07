import os

from pathlib import Path


def create_dirname(fname):
    os.makedirs(os.path.dirname(fname), exist_ok=True)


def create_dir(dname, parents=True):
    path = Path(dname)
    path.mkdir(parents=parents, exist_ok=True)
