# pylint: disable=C0111
import locale
import subprocess
import time
from contextlib import contextmanager

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.obal import get_specfile_evr  # pylint:disable=import-error,no-name-in-module


@contextmanager
def en_locale():
    """
    A context maanger that temporarily sets the LC_TIME locale to
    en_US.UTF-8 and then resets it.
    """
    try:
        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    except locale.Error:
        yield
    else:
        try:
            yield
        finally:
            locale.resetlocale(locale.LC_TIME)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            spec=dict(required=True),
            changelog=dict(default='- rebuilt')
        )
    )

    spec = module.params['spec']
    changelog = module.params['changelog']

    user = subprocess.check_output(['rpmdev-packager']).strip()
    evr = get_specfile_evr(spec)

    with open(spec) as spec_file:
        lines = spec_file.readlines()

    changed = False

    for i, line in enumerate(lines):
        if line.startswith("%changelog"):
            with en_locale():
                date = time.strftime("%a %b %d %Y", time.gmtime())
            entry = "* %s %s - %s\n%s\n\n" % (date, user, evr, changelog)
            lines[i] += entry
            changed = True
            break

    with open(spec, "w") as spec_file:
        spec_file.writelines(lines)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
