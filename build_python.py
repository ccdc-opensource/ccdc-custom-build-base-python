#!/usr/bin/env python3
import shutil
import subprocess
from pathlib import Path

python_version = '3.7.4'

def macos():
    return sys.platform == 'darwin'

def windows():
    return sys.platform == 'win32'

def linux():
    return sys.platform.startswith('linux')

def centos():
    return linux()

def install_from_msi():
    pass

def install_prerequisites():
    pass

def install_pyenv():
    if macos():
        subprocess.run(['brew', 'install', 'pyenv'], check=True)

def install_pyenv_version(version):
    python_destdir = Path('/opt/ccdc/third-party/python')
    version_destdir = python_destdir / f'python-{python_version}'
    if macos():
        pyenv_env = dict(os.environ)
        pyenv_env['PYENV_ROOT'] = str(python_destdir)
        subprocess.run(['pyenv', 'install', version], check=True)

def main():
    if sys.platform == 'win32':
        install_from_msi()
    else:
        install_prerequisites()
        install_pyenv()
        install_pyenv_version(python_version)
    

if __name__ == "__main__":
    main()
