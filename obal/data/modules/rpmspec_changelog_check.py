#!/usr/bin/env python

# pylint: disable=C0111,C0301,R1710

import os
import subprocess
import glob

from ansible.module_utils.basic import AnsibleModule  # pylint: disable=C0413
from ansible.module_utils.obal import get_changelog_evr, get_specfile_evr  # pylint:disable=import-error,no-name-in-module


ANSIBLE_METADATA = {
    'metadata_version': '1.2',
    'status': ['preview'],
    'supported_by': 'community'
}


def run_module():
    module_args = dict(
        directory=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        changelog_epoch_version_release='',
        specfile_epoch_version_release=''
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
        result['changelog_epoch_version_release'] = get_changelog_evr(specfile)

        result['specfile_epoch_version_release'] = get_specfile_evr(specfile)
    except subprocess.CalledProcessError as err:
        msg = "An error occured while running [ {} ]".format(err.cmd)
        module.fail_json(msg=msg, **result)

    if result['changelog_epoch_version_release'] != result['specfile_epoch_version_release']:
        msg = "changelog entry missing for {}".format(result['specfile_epoch_version_release'])
        module.fail_json(msg=msg, **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
