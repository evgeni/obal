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

def get_changelog_evr(specfile):
    evr = subprocess.check_output([
        'rpm',
        '--query',
        '--changelog',
        '--specfile',
        specfile
    ])
    return evr.split("\n")[0].split(" ")[-1]

def get_specfile_evr(specfile):
    return subprocess.check_output([
        'rpm',
        '--query',
        '--queryformat',
        '%|epoch?{%{epoch}:}:{}|%{version}-%{release}',
        '--undefine',
        'dist',
        '--specfile',
        specfile
    ])


def run_module():
    module_args = dict(
        directory=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        changelog=dict(
            epoch_version_release=''
        ),
        specfile=dict(
            epoch_version_release=''
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
        result['changelog']['epoch_version_release'] = get_changelog_evr(specfile)

        result['specfile']['epoch_version_release'] = get_specfile_evr(specfile)
    except subprocess.CalledProcessError as err:
        msg = "An error occured while running [ {} ]".format(err.cmd)
        module.fail_json(msg=msg, **result)

    if result['changelog']['epoch_version_release'] != result['specfile']['epoch_version_release']:
        msg = "changelog entry missing for {}".format(result['specfile']['epoch_version_release'])
        module.fail_json(msg=msg, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
