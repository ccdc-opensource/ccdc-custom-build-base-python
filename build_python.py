#!/usr/bin/env python3
import shutil
import subprocess
import sys
import os
from pathlib import Path
from ccdc.thirdparty.package import Package, AutoconfMixin, MakeInstallMixin, NoArchiveMixin, CMakeMixin


package_name = 'base_python'
python_version = '3.11.6'
macos_deployment_target = '10.15'


class InstallInBasePythonMixin(object):
    @property
    def install_directory(self):
        return python_version_destdir()


class SqlitePackage(InstallInBasePythonMixin, AutoconfMixin, NoArchiveMixin, Package):
    '''SQLite'''
    name = 'sqlite'
    version = '3.45.0'
    tarversion = '3450000'

    @property
    def source_archives(self):
        return {
            f'sqlite-autoconf-{self.tarversion}.tar.gz': f'https://www.sqlite.org/2024/sqlite-autoconf-{self.tarversion}.tar.gz'
        }

    @property
    def main_source_directory_path(self):
        return self.source_extracted / f'{self.name}-autoconf-{self.tarversion}'

    @property
    def cflags(self):
        return super().cflags + [
            '-DSQLITE_ENABLE_FTS3',
            '-DSQLITE_ENABLE_FTS3_PARENTHESIS',
            '-DSQLITE_ENABLE_FTS4',
            '-DSQLITE_ENABLE_FTS5',
            '-DSQLITE_ENABLE_EXPLAIN_COMMENTS',
            '-DSQLITE_ENABLE_NULL_TRIM',
            '-DSQLITE_MAX_COLUMN=10000',
            '-DSQLITE_ENABLE_JSON1',
            '-DSQLITE_ENABLE_RTREE',
            '-DSQLITE_TCL=0',
            '-fPIC',
        ]

    @property
    def ldflags(self):
        return super().ldflags + [
            '-lm'
        ]

    @property
    def arguments_to_configuration_script(self):
        return super().arguments_to_configuration_script + [
            '--enable-threadsafe',
            '--enable-shared=no',
            '--enable-static=yes',
            '--disable-readline',
            '--disable-dependency-tracking',
        ]


def macos():
    return sys.platform == 'darwin'

def windows():
    return sys.platform == 'win32'

def linux():
    return sys.platform.startswith('linux')

def centos():
    return linux() and Path('/etc/centos-release').exists()

def debian():
    return linux() and Path('/etc/debian_version').exists()

def ubuntu():
    return debian() and subprocess.check_output('lsb_release -i -s', shell=True).decode('utf-8').strip() == 'Ubuntu'

def platform():
    if linux():
        if centos():
            version = subprocess.check_output('rpm -E %{rhel}', shell=True).decode('utf-8').strip()
            return f'centos{version}'
        else:
            version = subprocess.check_output('lsb_release -r -s', shell=True).decode('utf-8').strip()
            return f'ubuntu{version}'
    return sys.platform

def output_base_name():
    components = [
        package_name,
        python_version,
    ]
    if 'BUILD_BUILDNUMBER' in os.environ:
        components.append(os.environ['BUILD_BUILDNUMBER'])
    else:
        components.append('dont-use-me-dev-build')
    components.append(platform())
    return '-'.join(components)

def python_destdir():
    if windows():
        return Path('D:\\x_mirror\\buildman\\tools\\base_python')
    else:
        return Path('/opt/ccdc/third-party/base_python')

def python_version_destdir():
    return python_destdir() / output_base_name()


def python_interpreter():
    if windows():
        return python_version_destdir() / 'python.exe'
    else:
        return python_version_destdir() / 'bin' / 'python'


def prepare_output_dir():
    if linux():
        subprocess.run(f'sudo mkdir -p {python_destdir()}', shell=True)
        subprocess.run(f'sudo chown $(id -u) {python_destdir()}', shell=True)


def install_from_msi():
    import urllib.request
    import tempfile
    url=f'https://www.python.org/ftp/python/{python_version}/python-{python_version}-amd64.exe'
    localfilename=f'python-{python_version}-amd64.exe'
    with tempfile.TemporaryDirectory() as tmpdir:
        localfile = Path(tmpdir) / localfilename
        print(f'Fetching {url} to {localfile}')
        with urllib.request.urlopen(url) as response:
            with open(localfile, 'wb') as final_file:
                shutil.copyfileobj(response, final_file)
        subprocess.run(f'{localfile} /quiet InstallAllUsers=0 Include_launcher=0 Include_doc=0 Include_debug=1 Include_symbols=1 Shortcuts=0 Include_test=0 CompileAll=1 TargetDir="{python_version_destdir()}" SimpleInstallDescription="Just for me, no test suite."', shell=True, check=True)


def install_prerequisites():
    if macos():
        subprocess.run(['brew', 'update'], check=True)
        subprocess.run(['brew', 'install', 'openssl', 'readline', 'sqlite3', 'xz', 'zlib', 'tcl-tk'], check=True)
    if linux():
        if centos():
            subprocess.run('sudo yum update -y', shell=True, check=True)
            subprocess.run('sudo yum install -y https://packages.microsoft.com/config/rhel/7/packages-microsoft-prod.rpm', shell=True, check=True)
            subprocess.run('sudo yum install -y epel-release', shell=True, check=True)
            subprocess.run('sudo yum install -y findutils gcc zlib-devel bzip2 bzip2-devel readline-devel openssl11-libs openssl11-devel tkinter tk tk-devel tcl-devel xz xz-devel libffi-devel patch powershell', shell=True, check=True)
            # See https://jira.ccdc.cam.ac.uk/browse/BLD-5684
            subprocess.run(f'sudo mkdir -p {python_version_destdir()}', shell=True)
            subprocess.run(f'sudo chown $(id -u) {python_version_destdir()}; echo "chown $(id -u) {python_version_destdir()}"', shell=True)
            SqlitePackage().build()

        if ubuntu():
            subprocess.run('sudo apt-get -y update', shell=True, check=True)
            subprocess.run('sudo apt-get -y dist-upgrade', shell=True, check=True)
            subprocess.run('sudo apt-get -y install make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev patch', shell=True, check=True)


def install_pyenv():
    if macos():
        subprocess.run(['brew', 'install', 'pyenv'], check=True)
    if linux():
        subprocess.run(['rm -rf /tmp/pyenvinst'], shell=True, check=True)
        subprocess.run(['git clone https://github.com/pyenv/pyenv.git /tmp/pyenvinst'], shell=True, check=True)


def install_pyenv_version(version):
    python_build_env = dict(os.environ)
    if macos():
        python_build_env['PATH'] = f"/usr/local/opt/tcl-tk/bin:{python_build_env['PATH']}"
        python_build_env['MACOSX_DEPLOYMENT_TARGET'] = macos_deployment_target
        python_build_env['LDFLAGS'] = "-L/usr/local/opt/tcl-tk/lib"
        python_build_env['CPPFLAGS'] = f"-I/usr/local/opt/tcl-tk/include -mmacosx-version-min={macos_deployment_target}"
        python_build_env['CFLAGS'] = f"-mmacosx-version-min={macos_deployment_target}"
        python_build_env['PKG_CONFIG_PATH'] = "/usr/local/opt/tcl-tk/lib/pkgconfig"
        python_build_env['PYTHON_CONFIGURE_OPTS'] = (
                "--with-tcltk-includes='-I/usr/local/opt/tcl-tk/include' "
                "--with-tcltk-libs='-L/usr/local/opt/tcl-tk/lib -ltcl8.6 -ltk8.6' "
                f"--with-macosx-version-min={macos_deployment_target}"
                )
        python_build_env['CONFIGURE_OPTS'] = f"--with-macosx-version-min={macos_deployment_target}"
        subprocess.run(f'sudo -E python-build {version} {python_version_destdir()}', shell=True, check=True, env=python_build_env)
        return
    if linux():
        python_build_env['PATH']=f"/tmp/pyenvinst/plugins/python-build/bin:{python_build_env['PATH']}"
        if centos():
            python_build_env['PATH']=f"{python_version_destdir()}/bin:{python_build_env['PATH']}"
            python_build_env['PYTHON_CONFIGURE_OPTS']="--enable-shared"
            subprocess.run(f"sed -i 's#\"${{!PACKAGE_CONFIGURE_OPTS_ARRAY}}\" $CONFIGURE_OPTS ${{!PACKAGE_CONFIGURE_OPTS}} || return 1#\"${{!PACKAGE_CONFIGURE_OPTS_ARRAY}}\" $CONFIGURE_OPTS --enable-shared LD_RUN_PATH={python_version_destdir()}/lib LD_LIBRARY_PATH={python_version_destdir()}/lib LDFLAGS=\"-L{python_version_destdir()}/lib -L/usr/lib64/openssl11 -lssl -lcrypto -L/usr/lib64 -ltcl8.5 -ltk8.5 -lz -lm -ldl -lpthread\" CPPFLAGS=\"-I{python_version_destdir()}/include -I/usr/include/openssl11\" ${{!PACKAGE_CONFIGURE_OPTS}} || return 1#' /tmp/pyenvinst/plugins/python-build/bin/python-build", shell=True, check=True, env=python_build_env)
            subprocess.run(f'grep CONFIGURE_OPTS /tmp/pyenvinst/plugins/python-build/bin/python-build', shell=True, check=True, env=python_build_env)
            subprocess.run(f'sudo -E /tmp/pyenvinst/plugins/python-build/bin/python-build -v {version} {python_version_destdir()}', shell=True, check=True, env=python_build_env)
            return
    subprocess.run(f'sudo env "PATH=$PATH" python-build {version} {python_version_destdir()}', shell=True, check=True, env=python_build_env)


def output_archive_filename():
    return f'{output_base_name()}.tar.gz'


def smoke_test():
    subprocess.check_call([f'{ python_interpreter() }', '-m', 'pip', 'install', 'packaging'])
    subprocess.check_call([f'{ python_interpreter() }', 'smoke_test.py'])


def create_archive():
    if 'BUILD_ARTIFACTSTAGINGDIRECTORY' in os.environ:
        archive_output_directory = Path(
            os.environ['BUILD_ARTIFACTSTAGINGDIRECTORY'])
    else:
        archive_output_directory = python_destdir() / 'packages'
    archive_output_directory.mkdir(parents=True, exist_ok=True)
    print(f'Creating {output_archive_filename()} in {archive_output_directory}')
    command = [
        'tar',
        '-zcf',
        f'{ archive_output_directory / output_archive_filename() }',  # the tar filename
        f'{ python_version_destdir().relative_to(python_destdir()) }',
    ]
    try:
        # keep the name + version directory in the archive, but not the package name directory
        subprocess.run(command, check=True, cwd=python_destdir())
    except subprocess.CalledProcessError as e:
        if not windows():
            raise e
        command.insert(1, '--force-local')
        # keep the name + version directory in the archive, but not the package name directory
        subprocess.run(command, check=True, cwd=python_destdir())


def main():
    prepare_output_dir()
    if sys.platform == 'win32':
        install_from_msi()
    else:
        install_prerequisites()
        install_pyenv()
        install_pyenv_version(python_version)
    smoke_test()
    create_archive()


if __name__ == "__main__":
    main()
