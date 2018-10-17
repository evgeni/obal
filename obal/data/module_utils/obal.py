"""
Ansible module helper functions for obal modules
"""
import subprocess

def get_changelog_evr(specfile):
    """get the EVR from the last changelog entry in the specfile"""
    evr = subprocess.check_output([
        'rpm',
        '--query',
        '--changelog',
        '--specfile',
        specfile
    ])
    return evr.split("\n")[0].split(" ")[-1]

def get_specfile_evr(specfile):
    """get the EVR from the source header of the specfile"""
    return subprocess.check_output([
        'rpmspec',
        '--query',
        '--queryformat',
        '%{evr}',
        '--undefine',
        'dist',
        '--srpm',
        specfile
    ])
