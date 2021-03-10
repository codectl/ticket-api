# -*- coding: utf-8 -*-
import argparse
import collections
import functools
import sys
import re
import os
import inspect

from manager import cli


class Error(Exception):
    pass


def puts(r):
    stdout = sys.stdout.write
    type_ = type(r)
    if type_ == list:
        return [puts(i) for i in r]
    elif type_ == dict:
        for key in r:
            puts(cli.blue(cli.min_width(key, 25) + str(r[key])))
        return
    elif type_ == Error:
        return puts(cli.red(str(r)))
    elif type_ == bool:
        if r:
            return puts(cli.green('OK'))
        return puts(cli.red('FAILED'))
    elif r is not None:
        return cli.puts(str(r).rstrip('\n'), stream=stdout)


class Command(object):
    name = None
    namespace = None
    description = 'no description'
    run = None
    capture_all = False

    def __init__(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise Exception('Invalid keyword argument `{key}`'.format(key=key))
        self.arg_names = list()
        self.args = list()

        if self.name is None:
            self.name = re.sub(
                '(.)([A-Z]{1})', r'\1_\2',
                self.__class__.__name__
            ).lower()

        if not self.capture_all:
            self.inspect()

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def inspect(self):
        self.arg_names, varargs, keywords, defaults, *_ = inspect.getfullargspec(
            self.run)
        if hasattr(self.run, 'im_self') or hasattr(self.run, '__self__'):
            del self.arg_names[0]  # Removes `self` arg for class method
        if defaults is not None:
            self.kwargs = dict(zip(
                *[reversed(l) for l in (self.arg_names, defaults)]
            ))
        else:
            self.kwargs = {}
        for arg_name in self.arg_names:
            type_ = type(self.kwargs.get(arg_name))
            if type_ == type(None):
                type_ = None
            default = self.kwargs.get(arg_name)
            flag = None
            if type_ == bool and default is True:
                flag = 'no-{arg_name}'.format(arg_name=arg_name)
            arg = Arg(arg_name, flag=flag, default=default, type=type_,
                      required=not arg_name in self.kwargs)
            self.add_argument(arg)

    def add_argument(self, arg):
        """ Adds the ```arg``` to the list of command's arguments

            @type arg: Arg
        """
        if self.has_argument(arg.name):
            raise Exception('Arg {name} already exists'.format(arg.name))
        self.args.append(arg)

    def get_argument(self, name):
        position = self.get_position(name)
        if position is None:
            raise Exception('Arg {} does not exist'.format(name))
        return self.args[position], position

    def get_position(self, name):
        for i, arg in enumerate(self.args):
            if name == arg.name:
                return i

    def has_argument(self, name):
        return name in (arg.name for arg in self.args)

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def parse(self, args):
        try:
            if self.capture_all:
                args, kwargs = [args], {}
            else:
                parsed_args = self.parser.parse_args(args)
                kwargs = dict(parsed_args._get_kwargs())
                args = []
                position = 0
                for arg_name in self.arg_names:
                    arg = self.args[position]
                    if not isinstance(arg, PromptedArg) and arg.required:
                        args.append(getattr(parsed_args, arg_name))
                        del kwargs[arg_name]
                    if isinstance(arg, PromptedArg):
                        args.append(arg.prompt())
                    position += 1
            r = self(*args, **kwargs)
            failed = r is False
        except Error as e:
            r = e
            failed = True
        puts(r)
        if failed:
            sys.exit(1)

    @property
    def parser(self):
        if self.namespace:
            prog = '%s %s.%s' % (sys.argv[0], self.namespace, self.name)
        else:
            prog = '%s %s' % (sys.argv[0], self.name)

        parser = argparse.ArgumentParser(prog=prog, description=self.description)
        for arg in self.args:
            if not isinstance(arg, PromptedArg):
                parser.add_argument(*arg.flags, **arg.kwargs)
        return parser

    @property
    def path(self):
        if self.namespace:
            return '.'.join([self.namespace, self.name])
        else:
            return self.name


class Manager(object):
    def __init__(self, base_command=Command, envs=False):
        self.base_command = base_command
        self.commands = {}
        self.env_vars = collections.defaultdict(dict)
        if envs:
            self.command(self.envs)

    @property
    def Command(self):
        manager = self

        class BoundMeta(type):
            def __new__(meta, name, bases, dict_):
                new = type.__new__(meta, name, bases, dict_)
                if name != 'BoundCommand':
                    manager.add_command(new())
                return new

        return BoundMeta('BoundCommand', (self.base_command, ), {})

    def add_command(self, command):
        self.commands[command.path] = command

    @staticmethod
    def arg(name, shortcut=None, positional=True, **kwargs):
        def wrapper(command):
            def wrapped(**kwargs):
                if command.has_argument(name):
                    arg, position = command.get_argument(name)
                    if shortcut is not None:
                        arg.shortcut = shortcut
                    if name in command.kwargs:
                        kwargs['default'] = command.kwargs[name]
                        kwargs['required'] = False
                    arg._kwargs.update(**kwargs)
                    return command
                try:
                    command.add_argument(Arg(name, shortcut=shortcut, **kwargs))
                except ValueError as exc:
                    raise ValueError(
                        "%s while adding argument to command %s:%s" % (
                            exc, command.run.__module__, command.name
                        )
                    )
                return command
            return wrapped(**kwargs)

        return wrapper

    def prompt(self, name, message=None, **kwargs):
        def wrapper(command):
            def wrapped(**kwargs):
                arg, position = command.get_argument(name)
                command.args[position] = PromptedArg(name, arg, message,
                    **kwargs)
                return command
            return wrapped(**kwargs)

        return wrapper

    def merge(self, manager, namespace=None):
        for command_name in manager.commands:
            command = manager.commands[command_name]
            if namespace is not None:
                command.namespace = namespace
            self.add_command(command)

    def command(self, *args, **kwargs):
        """ Decorator for command methods

            Unless overridden by the ```name``` argument, it will use the
            method's name as the command's name.

            The command's help string will be taken from the optional
            ```description``` named argument.

        """
        def register(fn):
            def wrapped(**kwargs):
                if not 'name' in kwargs:
                    kwargs['name'] = fn.__name__
                if not 'description' in kwargs and fn.__doc__:
                    kwargs['description'] = fn.__doc__
                command = self.Command(run=fn, **kwargs)
                self.add_command(command)
                return command
            return wrapped(**kwargs)

        if len(args) == 1 and callable(args[0]):
            fn = args[0]
            return register(fn)
        else:
            return register

    def update_env(self, setdefault=True):
        path = os.path.join(os.getcwd(), '.env')
        if not os.path.isfile(path):
            return

        with open(path) as f:
            content = f.read()

        items = list(self.parse_env(content))

        if setdefault:
            setter = os.environ.setdefault
            items = reversed(items)
        else:
            setter = os.environ.__setitem__

        for key, value in items:
            setter(key, value)

    def parse_env(self, content):
        def strip_quotes(string):
            for quote in "'", '"':
                if string.startswith(quote) and string.endswith(quote):
                    return string.strip(quote)
            return string

        regexp = re.compile('^([A-Za-z_0-9]+)=(.*)$', re.MULTILINE)
        founds = re.findall(regexp, content)
        return ((key, strip_quotes(value)) for key, value in founds)

    @property
    def parser(self):
        if any([c.namespace for c in self.commands.values()]):
            usage='%(prog)s [<namespace>.]<command> [<args>]'
        else:
            usage='%(prog)s <command> [<args>]'

        parser = argparse.ArgumentParser(usage=usage)
        parser.add_argument('command', help='the command to run')
        return parser

    def usage(self):
        def format_line(command, w):
            return "%s%s" % (
                cli.min_width(command.name, w), command.description
            )

        self.parser.print_help()
        if len(self.commands) > 0:
            puts('\navailable commands:')
            with cli.indent(2):
                namespace = None
                for command_path in sorted(
                        self.commands,
                        key=lambda c: '%s%s' % (c.count('.'), c)
                ):
                    command = self.commands[command_path]
                    if command.namespace is not None:
                        if command.namespace != namespace:
                            puts(cli.red('\n[%s]' % command.namespace))
                        with cli.indent(2):
                            puts(format_line(command, 23))
                    else:
                        puts(format_line(command, 25))
                    namespace = command.namespace

    def main(self, args=None):
        args = cli.Args(args)
        if len(args) == 0 or args[0] in ('-h', '--help'):
            return self.usage()

        command = args.get(0)
        try:
            command = self.commands[command]
        except KeyError:
            puts(cli.red('Invalid command `%s`\n' % command))
            return self.usage()
        self.update_env()
        command.parse(args.all[1:])

    def env(self, key, value=None):
        """Decorator to register an ENV variable needed for a method.

        For optional env variables, set a default value using <value>.

        All env vars will be made available as key word arguments.

        @manager.env('SOME_ARG')
        def your_method(some_arg):
            ...
        """
        key = key.lower()

        def decorator(f):
            self.env_vars[f.__name__][key] = value

            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                if kwargs.get(key, None) is None:
                    if key.upper() in os.environ:
                        kwargs[key] = os.environ[key.upper()]
                    elif value:
                        kwargs[key] = value
                    else:
                        raise KeyError('Please set ENV var %s.' % key.upper())
                return f(*args, **kwargs)
            return wrapper
        return decorator

    def envs(self):
        """List required and optional environment variables."""
        if not self.env_vars:
            puts('No ENV variables have been registered.')
            puts('To register an ENV variable, use the @env(key, value) ')
            puts('method decorator of your manager object.')
            return

        puts('Registered ENV vars per method.\n')
        for func_name in self.env_vars:
            puts('%s:' % func_name)
            for var, default in self.env_vars[func_name].items():
                default = '(%s)' % default if default is not None else ''
                puts('\t%s%s' % (cli.min_width(var.upper(), 30), default))
            puts('')


class Arg(object):
    defaults = {
        'help': 'no description',
        'required': False,
        'type': None,
    }

    def __init__(self, name, flag=None, shortcut=None, **kwargs):
        if kwargs.get('default') and kwargs.get('help'):
            kwargs['help'] = '%s (default: %s)' % (kwargs['help'], kwargs['default'])

        self.name = name
        self.flag = flag if flag is not None else name
        self.shortcut = shortcut
        self._kwargs = self.defaults.copy()
        self._kwargs.update(kwargs)
        if self.type == bool and 'default' not in kwargs:
            raise ValueError(
                "No default value provided for boolean argument '%s'" % name
            )

    def __getattr__(self, key):
        if not key in self._kwargs:
            raise AttributeError(key)
        return self._kwargs[key]

    @property
    def flags(self):
        flags = [self.flag]
        if not self.required:
            flags = ['--%s' % self.flag.replace('_', '-')]
            if self.shortcut is not None:
                flags.insert(0, '-%s' % self.shortcut)
        return flags

    @property
    def kwargs(self):
        dict_ = self._kwargs.copy()

        if self.required:
            del dict_['required']
        else:
            dict_.setdefault('dest', self.name)

            if self.type == bool:
                if self.default:
                    dict_['action'] = 'store_false'
                else:
                    dict_['action'] = 'store_true'

                dict_.pop('type', None)
        return dict_


class PromptedArg(Arg):
    def __init__(self, name, arg, message=None, **kwargs):
        self.name = name
        self.message = message if message is not None else name
        self._kwargs = {
            'empty': not arg.required,
            'type': str if arg.type is None else arg.type,
            'default': arg.default,
        }
        self._kwargs.update(kwargs)

    @property
    def kwargs(self):
        return self._kwargs

    def prompt(self):
        return cli.prompt(self.message, **self.kwargs)
