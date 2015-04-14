import sys
from optparse import make_option
from optparse import NO_DEFAULT, OptionParser
from django.core.management.base import CommandError, BaseCommand
from django.core.management.base import handle_default_options
from django.utils.importlib import import_module


class Command(BaseCommand):
    help = "A wrapper for REDCap subcommands"

    subcommands = {'inspect': 'inspect',
                   'json': 'rjson',
                   'models': 'models',
                   'fixture': 'fixture',
                   'convert': 'convert'
                   }

    def print_subcommands(self, prog_name):
        usage = ['', 'Available subcommands:']
        for name in sorted(self.subcommands):
            usage.append('  {0}'.format(name))
        return '\n'.join(usage)

    def usage(self, subcommand):
        usage = '%prog {0} subcommand [options] [args]'.format(subcommand)
        if self.help:
            return '{0}\n\n{1}'.format(usage, self.help)
        return usage

    def print_help(self, prog_name, subcommand):
        super(Command, self).print_help(prog_name, subcommand)
        sys.stdout.write('{0}\n\n'.format(self.print_subcommands(prog_name)))

    def get_subcommand(self, name):
        try:
            module = import_module('djredcap.management.subcommands.{0}'
                                   .format(self.subcommands[name]))
            return module.Command()
        except KeyError:
            raise CommandError('Unknown subcommand: djredcap {0}'.format(name))

    def run_from_argv(self, argv):
        """Set up any environment changes requested (e.g., Python path
        and Django settings), then run this command.
        """
        if len(argv) > 2 and not argv[2].startswith('-') and \
                argv[2] in self.subcommands.keys():
            subcommand = argv[2]
            klass = self.get_subcommand(subcommand)
            parser = OptionParser(prog=argv[0],
                                  usage=klass.usage('{0} {1}'
                                                    .format(argv[1],
                                                            subcommand)),
                                  version=klass.get_version(),
                                  option_list=klass.option_list)
            options, args = parser.parse_args(argv[3:])
            args = [subcommand] + args
        else:
            parser = self.create_parser(argv[0], argv[1])
            options, args = parser.parse_args(argv[2:])

        handle_default_options(options)
        self.execute(*args, **options.__dict__)

    def handle(self, *args, **options):
        if not args or args[0] not in self.subcommands.keys():
            return self.print_help('./manage.py', 'redcap')
        subcommand, args = args[0], args[1:]

        klass = self.get_subcommand(subcommand)
        # Grab out a list of defaults from the options. optparse does this for
        # us when the script runs from the command line, but since
        # call_command can be called programatically, we need to simulate the
        # loading and handling of defaults (see #10080 for details).
        defaults = {}
        for opt in klass.option_list:
            if opt.default is NO_DEFAULT:
                defaults[opt.dest] = None
            else:
                defaults[opt.dest] = opt.default
        defaults.update(options)

        return klass.execute(*args, **defaults)
