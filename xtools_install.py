#!/usr/bin/env python
##
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
##
##
# @file   xtools_install.py
# @author Cesar Fuguet Tortolero
##

"""This script installs a cross-toolchain for a given target architecture
"""

# TODO: check output status of subprocess calls

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__author__ = 'Cesar Fuguet Tortolero'
__version__ = '1.0.0'

import os
import errno
import tarfile
import subprocess

TARGET = 'riscv64-unknown-elf'
PREFIX_DIR = '/home/360.1.361-EPI/xtools/riscv64-unknown-elf-vrp'
SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))

CONFIG = {
    'target'            : TARGET,
    'binutils_version'  : '2.32',
    'gcc_version'       : '9.2.0',
    'gdb_version'       : '8.3',
    'gmp_version'       : '6.1.0',
    'mpfr_version'      : '3.1.4',
    'mpc_version'       : '1.0.3',
    'isl_version'       : '0.18',
    'nparallel'         : 3,

    # base directories shared by all tools
    'archive_dir'       : os.path.join(SCRIPT_DIR, 'archives'),
    'src_dir'           : os.path.join(SCRIPT_DIR, 'src'),
    'build_dir'         : os.path.join(SCRIPT_DIR, 'build'),
    'install_dir'       : PREFIX_DIR,
}


class ToolPackage(object):
    """ Generic class for describing a tool package
    """
    def __init__(self, name, version, tar_extension):
        """ This function initialize package attributes
        """
        self.name = name
        self.version = version
        self.tar_extension = tar_extension

    def get_full_name(self):
        """ This function returns full name of package (name + version)
        """
        return self.name + '-' + self.version

    def get_src(self):
        """ This function returns full path to the package source directory
        """
        return os.path.join(CONFIG['src_dir'], self.get_full_name())

    def get_build(self):
        """ This function returns full path to the package build directory
        """
        return os.path.join(CONFIG['build_dir'], self.get_full_name())

    def get_tar(self):
        """ This function returns full path to the package tar file
        """
        tar_file = self.get_full_name() + self.tar_extension
        return os.path.join(CONFIG['archive_dir'], tar_file)

    def download(self, url):
        if os.path.exists(self.get_src()):
            print('The package sources are already extracted.. do nothing')
            return True
        if os.path.exists(self.get_tar()):
            print('The package archive are already downloaded.. do nothing')
            return True
        if not os.path.exists(CONFIG['archive_dir']):
            os.mkdir(CONFIG['archive_dir'])
        print('Fetching from', url)
        cmd = ['wget', '--tries=5', '-q', '-O', self.get_tar(), url]
        returncode = subprocess.call(cmd)
        return True if returncode == 0 else False

    def extract(self):
        """ This function extracts the package tar file
        """
        if not os.path.lexists(self.get_tar()):
            raise IOError(self.get_tar() + ' file not found')
        if not os.path.exists(CONFIG['src_dir']):
            os.mkdir(CONFIG['src_dir'])
        if not os.path.exists(self.get_src()):
            tar = tarfile.open(name=self.get_tar(), mode='r')
            tar.extractall(path=CONFIG['src_dir'])
            tar.close()
        else:
            print('The package was already extracted.. do nothing')

    def build(self):
        """ This function prepares the package for its building
        """
        if not os.path.exists(CONFIG['build_dir']):
            os.mkdir(CONFIG['build_dir'])
        if not os.path.exists(self.get_build()):
            os.mkdir(self.get_build())

        # go to the build directory
        os.chdir(self.get_build())

    def install(self):
        """ This function prepares the package for its installation
        """
        if not os.path.exists(CONFIG['install_dir']):
            print('The installation directory does not exists')
            return
        if not os.access(CONFIG['install_dir'], os.W_OK):
            print('The installation directory has not write permissions')
            return

        # go to the build directory
        os.chdir(self.get_build())


class BinutilsPackage(ToolPackage):
    """ Class for describing a binutils package
    """
    repos_url = (
        'http://ftpmirror.gnu.org/binutils',
        'http://ftp.gnu.org/gnu/binutils',
    )

    def download(self):
        for base_url in BinutilsPackage.repos_url:
            url = (
                base_url + '/' +
                self.get_full_name() + self.tar_extension
            )
            if super(BinutilsPackage, self).download(url):
                return True

        return False

    def _configure(self):
        """ This function configures the BINUTILS package for the target
        architecture
        """
        cmd = [
            os.path.join(self.get_src(), 'configure'),
            '--prefix=' + CONFIG['install_dir'],
            '--target=' + CONFIG['target'],
            '--program-prefix=' + CONFIG['target'] + '-',
            '--disable-nls',
            '--disable-multilib',
            '--disable-werror',
        ]
        subprocess.call(cmd)

    def build(self):
        """ This function builds the BINUTILS package for the target
        architecture
        """
        super(BinutilsPackage, self).build()

        # configure
        if os.path.lexists('Makefile'):
            print('A Makefile already exists in the build directory... '
                  'Skip configure')
        else:
            self._configure()

        # build
        cmd = ['make', '-j' + str(CONFIG['nparallel'])]
        subprocess.call(cmd)

    def install(self):
        super(BinutilsPackage, self).install()

        # install
        cmd = ['make', 'install']
        subprocess.call(cmd)


class GccPackage(ToolPackage):
    """ Class for describing a GCC package
    """
    repos_url = (
        'http://ftpmirror.gnu.org/gcc',
        'ftp://ftp.gnu.org/gnu/gcc',
    )

    def download(self):
        for base_url in GccPackage.repos_url:
            url = (
                base_url + '/' +
                self.get_full_name() + '/' +
                self.get_full_name() + self.tar_extension
            )
            if super(GccPackage, self).download(url):
                return True

        return False

    def _configure(self):
        """ This function configures the GCC package for the target
        architecture
        """
        cmd = [
            os.path.join(self.get_src(), 'configure'),
            '--prefix=' + CONFIG['install_dir'],
            '--target=' + CONFIG['target'],
            '--program-prefix=' + CONFIG['target'] + '-',
            '--disable-nls',
            '--disable-multilib',
            '--disable-werror',
            '--without-headers',
            '--enable-languages=c,c++',
        ]
        subprocess.call(cmd)

    def prerequisites(self):
        """ Install GCC required packages into its source directory
        """
        # go to the src directory
        os.chdir(self.get_src())

        # call the contrib script in the GCC source directory. This script
        # downloads the GCC prerequisites
        cmd = [
            os.path.join(self.get_src(), 'contrib/download_prerequisites'),
        ]
        subprocess.call(cmd)

    def build(self):
        """ This function builds the GCC package for the target architecture
        """
        super(GccPackage, self).build()

        # prepare the GCC prerequisites
        self.prerequisites()

        # go to the build directory
        os.chdir(self.get_build())

        # configure
        if os.path.lexists('Makefile'):
            print('A Makefile already exists in the build directory... '
                  'Skip configure')
        else:
            self._configure()

        # build
        cmd = ['make', '-j' + str(CONFIG['nparallel']), 'all-gcc']
        subprocess.call(cmd)
        cmd = ['make', '-j' + str(CONFIG['nparallel']), 'all-target-libgcc']
        subprocess.call(cmd)

    def install(self):
        super(GccPackage, self).install()

        # install
        cmd = ['make', 'install-gcc']
        subprocess.call(cmd)
        cmd = ['make', 'install-target-libgcc']
        subprocess.call(cmd)


class GdbPackage(ToolPackage):
    """ Class for describing a GDB package
    """
    repos_url = (
        'http://ftpmirror.gnu.org/gdb',
        'http://ftp.gnu.org/gnu/gdb',
    )

    def download(self):
        for base_url in GdbPackage.repos_url:
            url = (
                base_url + '/' +
                self.get_full_name() + self.tar_extension
            )
            if super(GdbPackage, self).download(url):
                return True

        return False

    def _configure(self):
        """ This function configures the GDB package for the target
        architecture
        """
        cmd = [
            os.path.join(self.get_src(), 'configure'),
            '--prefix=' + CONFIG['install_dir'],
            '--target=' + CONFIG['target'],
            '--program-prefix=' + CONFIG['target'] + '-',
            '--enable-tui',
        ]
        subprocess.call(cmd)

    def build(self):
        """ This function builds the GDB package for the target architecture
        """
        super(GdbPackage, self).build()

        # configure
        if os.path.lexists('Makefile'):
            print('A Makefile already exists in the build directory... '
                  'Skip configure')
        else:
            self._configure()

        # build
        cmd = ['make', '-j' + str(CONFIG['nparallel']), 'all-gdb']
        subprocess.call(cmd)

    def install(self):
        super(GdbPackage, self).install()

        # install
        cmd = ['make', 'install-gdb']
        subprocess.call(cmd)


def main():
    """ Main routine
    """
    print('Building', CONFIG['target'], 'cross-compiler')
    print('Archives directory:', CONFIG['archive_dir'])
    print('Sources directory:', CONFIG['src_dir'])
    print('Build directory:', CONFIG['build_dir'])
    print('Install directory:', CONFIG['install_dir'])

    packages = (
        BinutilsPackage('binutils', CONFIG['binutils_version'], '.tar.gz'),
        GccPackage('gcc', CONFIG['gcc_version'], '.tar.gz'),
        GdbPackage('gdb', CONFIG['gdb_version'], '.tar.gz'),
    )
    for pkg in packages:
        print('Downloading', pkg.get_tar(), '...')
        pkg.download()
        print('Extracting', pkg.get_full_name(), '...')
        pkg.extract()
        print('Building', pkg.get_full_name(), '...')
        pkg.build()
        print('Installing', pkg.get_full_name(), '...')
        pkg.install()


if __name__ == '__main__':
    main()
