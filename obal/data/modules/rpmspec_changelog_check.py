#!/usr/bin/env python

# pylint: disable=C0111,C0301,R1710

import os
import subprocess
import glob

ANSIBLE_METADATA = {
    'metadata_version': '1.2',
    'status': ['preview'],
    'supported_by': 'community'
}

from ansible.module_utils.basic import AnsibleModule  # pylint: disable=C0413

def get_changelog_epoch_version_release(specfile):
    cmd = ['rpm', '--query', '--changelog', '--specfile', specfile]

    return subprocess.check_output(cmd).split("\n")[0].split(" ")[-1]


def format_evr(epoch, version, release):
    epoch = epoch.strip().replace('"', '')
    version = version.strip().replace('"', '')
    release = release.strip().replace('"', '')
    evr = ""

    if not '(none)' in epoch:
        evr += "{}:".format(epoch)
    evr += "{}-{}".format(version, release)
    return evr


def run_module():
    module_args = dict(
        directory=dict(type='str', required=True),
    )

    result = dict(
        changed = False,
        changelog = dict(
            epoch_version_release = ''
        ),
        specfile = dict(
            epoch = '',
            version = '',
            release = ''
        )
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        return result

    try:
        specfile = glob.glob(os.path.join(module.params['directory'], "*.spec"))[0]
    except IndexError:
        module.fail_json(msg="Could not find specfile", **result)

    try:
        result['changelog']['epoch_version_release'] = get_changelog_epoch_version_release(specfile)

        result['specfile']['epoch'] = subprocess.check_output([
            'rpmspec',
            '--query',
            '--queryformat="%{epoch}"',
            '--srpm',
            specfile
        ])

        result['specfile']['version'] = subprocess.check_output([
            'rpmspec',
            '--query',
            '--queryformat="%{version}"',
            '--srpm',
            specfile
        ])

        result['specfile']['release'] = subprocess.check_output([
            'rpmspec',
            '--query',
            '--queryformat="%{release}"',
            '--srpm',
            '--undefine',
            'dist',
            specfile
        ])
    except subprocess.CalledProcessError as err:
        msg = "An error occured while running [ {} ]".format(err.cmd)
        module.fail_json(msg=msg, **result)

    evr = format_evr(result['specfile']['epoch'], result['specfile']['version'], result['specfile']['release'])

    if result['changelog']['epoch_version_release'] != evr:
        msg = "changelog entry missing for {}".format(evr)
        module.fail_json(msg=msg, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
