import os
import pytest
import obal


FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'fixtures',
)

DEFAULT_ARGS = ['dummy.yml', '--inventory', 'inventory.yml']


def test_find_no_packages():
    packages = obal.find_packages(os.path.join(FIXTURE_DIR, 'nope.yaml'))
    assert packages is None


def test_find_packages():
    packages = obal.find_packages(os.path.join(FIXTURE_DIR, 'inventory.yaml'))
    assert packages
    assert 'testpackage' in packages


def _test_generate_ansible_args(cliargs):
    parser = obal.obal_argument_parser(['testpackage'])
    args = parser.parse_args(cliargs)
    ansible_args = obal.generate_ansible_args('inventory.yml', 'dummy.yml',
                                              args)
    return ansible_args


def test_generate_ansible_args_none():
    with pytest.raises(SystemExit):
        _test_generate_ansible_args([])


@pytest.mark.parametrize('cliargs,expected', [
    (['scratch', 'testpackage'],
     DEFAULT_ARGS + ['--limit', 'testpackage']),
    (['scratch', 'testpackage', '--verbose'],
     DEFAULT_ARGS + ['--limit', 'testpackage', '-v']),
    (['scratch', 'testpackage', '-vvvv'],
     DEFAULT_ARGS + ['--limit', 'testpackage', '-vvvv']),
    (['scratch', 'testpackage', '--step'],
     DEFAULT_ARGS + ['--limit', 'testpackage', '--step']),
    (['scratch', 'testpackage', '--skip-tags', 't1,t2'],
     DEFAULT_ARGS + ['--limit', 'testpackage', '--skip-tags', 't1,t2']),
    (['scratch', 'testpackage', '--tags', 'wait,download'],
     DEFAULT_ARGS + ['--limit', 'testpackage', '--tags', 'wait,download']),
    (['scratch', 'testpackage', '-e', 'v1=1', '-e', 'v2=2'],
     DEFAULT_ARGS + ['--limit', 'testpackage', '-e', 'v1=1', '-e', 'v2=2']),
])
def test_generate_ansible_args(cliargs, expected):
    ansible_args = _test_generate_ansible_args(cliargs)
    assert ansible_args == expected
