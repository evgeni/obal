#!/usr/bin/env python2
# PYTHON_ARGCOMPLETE_OK

from __future__ import print_function

import argparse
import os
import sys
import json

from pkg_resources import resource_filename

try:
    import argcomplete
except ImportError:
    argcomplete = None


class VariableAction(argparse.Action):
    """thanks ewoud! :)"""
    def __call__(self, parser, namespace, values, option_string=None):
        variables = getattr(namespace, self.dest)
        if variables is None:
            variables = {}
            setattr(namespace, self.dest, variables)

        if not option_string:
            # TODO: Can we still know this?
            raise ValueError('Unknown option')
        if option_string.startswith('--'):
            option_string = option_string[2:]
        variables[option_string] = values


def find_packages(inventory_path):
    package_choices = None
    if os.path.exists(inventory_path):
        from ansible.inventory.manager import InventoryManager
        from ansible.parsing.dataloader import DataLoader
        ansible_loader = DataLoader()
        ansible_inventory = InventoryManager(loader=ansible_loader,
                                             sources=inventory_path)
        package_choices = list(ansible_inventory.hosts.keys())
        package_choices.extend(ansible_inventory.groups.keys())
        package_choices.extend(['all'])
    return package_choices


def obal_argument_parser(package_choices):
    parser = argparse.ArgumentParser()

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-e', '--extra-vars',
                               dest="extra_vars",
                               action="append",
                               default=[],
                               help="""set additional variables as key=value or
                               YAML/JSON, if filename prepend with @""")
    parent_parser.add_argument("-v", "--verbose",
                               action="count",
                               dest="verbose",
                               help="verbose output")
    parent_parser.add_argument("--step",
                               action="store_true",
                               dest="step",
                               default=False,
                               help="interactive: confirm each task before running")
    parent_parser.add_argument('-t', '--tags',
                               dest='tags',
                               default=[],
                               action='append',
                               help="""only run plays and tasks tagged with these
                               values""")
    parent_parser.add_argument('--skip-tags',
                               dest='skip_tags',
                               default=[],
                               action='append',
                               help="""only run plays and tasks whose tags do not
                               match these values""")

    package_parser = argparse.ArgumentParser(add_help=False)
    package_parser.add_argument('package',
                                metavar='package',
                                choices=package_choices,
                                nargs='+',
                                help="the package to build")

    subparsers = parser.add_subparsers(dest='action',
                                       help="""which action to execute""")
    # Setting `required` outside of #add_subparser() is needed because
    # python2's #add_subparser() won't accept `required` as a field (even
    # though it's in the docs).
    subparsers.required = True

    subparsers.add_parser('bump-release', help="", parents=[parent_parser, package_parser])

    changelog_parser = subparsers.add_parser('changelog',
                                             help="write an RPM changelog entry"
                                             "for the current version and release",
                                             parents=[parent_parser, package_parser])
    changelog_parser.add_argument('--changelog', help="the changelog entry to add",
                                  dest='variables', metavar="MESSAGE", action=VariableAction)

    subparsers.add_parser('scratch', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('setup', help="", parents=[parent_parser])
    subparsers.add_parser('lint', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('update', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('nightly', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('source', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('add', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('release', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('cleanup-copr', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('srpm', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('repoclosure', help="", parents=[parent_parser, package_parser])
    subparsers.add_parser('check', help="", parents=[parent_parser, package_parser])

    if argcomplete:
        argcomplete.autocomplete(parser)

    return parser


def generate_ansible_args(inventory_path, playbook_path, args):
    ansible_args = [playbook_path, '--inventory', inventory_path]
    if hasattr(args, 'package'):
        limit = ':'.join(args.package)
        ansible_args.extend(['--limit', limit])
    if args.verbose:
        ansible_args.append("-%s" % str("v" * args.verbose))
    for extra_var in args.extra_vars:
        ansible_args.extend(["-e", extra_var])
    if 'variables' in args and args.variables:
        ansible_args.extend(["-e", json.dumps(args.variables)])
    if args.tags:
        ansible_args.append("--tags")
        ansible_args.append(",".join(args.tags))
    if args.skip_tags:
        ansible_args.append("--skip-tags")
        ansible_args.append(",".join(args.skip_tags))
    if args.step:
        ansible_args.append("--step")
    return ansible_args


def main(cliargs=None):
    data_path = resource_filename(__name__, 'data')
    packaging_playbooks_path = os.path.join(data_path, 'playbooks')
    cfg_path = os.path.join(data_path, 'ansible.cfg')

    if os.path.exists(cfg_path):
        os.environ["ANSIBLE_CONFIG"] = cfg_path

    # this needs to be global, as otherwise PlaybookCLI fails
    # to set the verbosity correctly
    from ansible.utils.display import Display
    global display
    display = Display()

    inventory_path = os.path.join(os.getcwd(), 'package_manifest.yaml')

    package_choices = find_packages(inventory_path)

    parser = obal_argument_parser(package_choices)

    args = parser.parse_args(cliargs)

    playbook_path = os.path.join(packaging_playbooks_path, '{}.yml'.format(args.action))

    if not args.action == 'setup':
        if not os.path.exists(inventory_path):
            print("Could not find your package_manifest.yaml")
            exit(1)
    if not os.path.exists(playbook_path):
        print("Could not find the packaging playbooks")
        exit(1)

    from ansible.cli.playbook import PlaybookCLI

    ansible_args = generate_ansible_args(inventory_path, playbook_path, args)
    ansible_playbook = (["ansible-playbook"] + ansible_args)

    if args.verbose:
        print(ansible_playbook)

    cli = PlaybookCLI(ansible_playbook)
    cli.parse()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
