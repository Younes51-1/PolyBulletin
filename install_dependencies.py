import subprocess
import sys
import importlib


def install_library(library_name):
    try:
        print(f"Trying to import {library_name}...", end='')
        importlib.import_module(library_name)
        print(f"{library_name.capitalize()} is installed")
    except ModuleNotFoundError:
        print(f"{library_name.capitalize()} not found, trying to install...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", library_name])
        print("\n\n\n\nDone.")


if __name__ == '__main__':
    install_library("configparser")
    install_library("selenium")
    install_library("aspose-words")
    install_library("DateTime")
    install_library("pytest-shutil")
