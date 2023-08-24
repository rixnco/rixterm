import inspect
import os
import sys
import importlib.util
import serial
from serial.tools import miniterm
from serial.tools.miniterm import *
from filters import FilterBase
from filters import SendOnEnter


try:
    raw_input
except NameError:
    # pylint: disable=redefined-builtin,invalid-name
    raw_input = input   # in python3 it's "raw"
    unichr = chr


def load_python_module(name, pathname):
    spec = importlib.util.spec_from_file_location(name, pathname)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def load_monitor_filters(monitor_dir, prefix=None, terminal=None, quiet=True):
    if not os.path.isdir(monitor_dir):
        return
    for name in os.listdir(monitor_dir):
        if (prefix and not name.startswith(prefix)) or not name.endswith(".py"):
            continue
        path = os.path.join(monitor_dir, name)
        if not os.path.isfile(path):
            continue
        load_monitor_filter(path, terminal, quiet)


def load_monitor_filter(path, terminal=None, quiet=True):
    name = os.path.basename(path)
    name = name[: name.find(".")]
    module = load_python_module("filters.%s" % name, path)
    for cls in get_object_members(module).values():
        if (
            not inspect.isclass(cls)
            or not issubclass(cls, FilterBase)
            or cls == FilterBase
        ):
            continue
        obj = cls(terminal)
        miniterm.TRANSFORMATIONS[obj.NAME] = obj
        if not quiet:
            print('--- Found filter: \'%s\' ---' % obj.NAME) 
    return True

def get_object_members(obj, ignore_private=True):
    members = inspect.getmembers(obj, lambda a: not inspect.isroutine(a))
    if not ignore_private:
        return members
    return {
        item[0]: item[1]
        for item in members
        if not (item[0].startswith("__") and item[0].endswith("__"))
    }


class Terminal(miniterm.Miniterm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def reader(self):
        try:
            super().reader()
        except Exception as exc:  # pylint: disable=broad-except
            pass

    def writer(self):
        try:
            super().writer()
        except Exception as exc:  # pylint: disable=broad-except
            pass

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# default args can be used to override when calling main() from an other script
# e.g to create a miniterm-my-device.py
def main(default_port=None, default_baudrate=115200, default_rts=None, default_dtr=None, serial_instance=None, default_eol='CRLF'):
    """Command line tool, entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Miniterm - A simple terminal program for the serial port.')

    parser.add_argument(
        'port',
        nargs='?',
        help='serial port name ("-" to show port list)',
        default=default_port)

    parser.add_argument(
        'baudrate',
        nargs='?',
        type=int,
        help='set baud rate, default: %(default)s',
        default=default_baudrate)

    group = parser.add_argument_group('port settings')

    group.add_argument(
        '--parity',
        choices=['N', 'E', 'O', 'S', 'M'],
        type=lambda c: c.upper(),
        help='set parity, one of {N E O S M}, default: N',
        default='N')

    group.add_argument(
        '--data',
        choices=[5, 6, 7, 8],
        type=int,
        help='set data bits, default: %(default)s',
        default=8)

    group.add_argument(
        '--stop',
        choices=[1, 2, 3],
        type=int,
        help='set stop bits (1, 2, 1.5), default: %(default)s',
        default=1)

    group.add_argument(
        '--rtscts',
        action='store_true',
        help='enable RTS/CTS flow control (default off)',
        default=False)

    group.add_argument(
        '--xonxoff',
        action='store_true',
        help='enable software flow control (default off)',
        default=False)

    group.add_argument(
        '--rts',
        type=int,
        help='set initial RTS line state (possible values: 0, 1)',
        default=default_rts)

    group.add_argument(
        '--dtr',
        type=int,
        help='set initial DTR line state (possible values: 0, 1)',
        default=default_dtr)

    group.add_argument(
        '--non-exclusive',
        dest='exclusive',
        action='store_false',
        help='disable locking for native ports',
        default=True)

    group.add_argument(
        '--ask',
        action='store_true',
        help='ask again for port when open fails',
        default=False)

    group = parser.add_argument_group('data handling')

    group.add_argument(
        '-e', '--echo',
        action='store_true',
        help='enable local echo (default off)',
        default=False)

    group.add_argument(
        '--encoding',
        dest='serial_port_encoding',
        metavar='CODEC',
        help='set the encoding for the serial port (e.g. hexlify, Latin1, UTF-8), default: %(default)s',
        default='UTF-8')

    group.add_argument(
        '-f', '--filter',
        action='append',
        metavar='NAME',
        help='add text transformation',
        default=[])

    group.add_argument(
        '--filter_dir',
        metavar='DIR',
        help='directory where to look for additional filters',
        default='filters')

    group.add_argument(
        '--eol',
        choices=['CR', 'LF', 'CRLF'],
        type=lambda c: c.upper(),
        help='end of line mode',
        default=default_eol)

    group.add_argument(
        '--raw',
        action='store_true',
        help='Do no apply any encodings/transformations',
        default=False)

    group = parser.add_argument_group('hotkeys')

    group.add_argument(
        '--exit-char',
        type=int,
        metavar='NUM',
        help='Unicode of special character that is used to exit the application, default: %(default)s',
        default=0x1d)  # GS/CTRL+]

    group.add_argument(
        '--menu-char',
        type=int,
        metavar='NUM',
        help='Unicode code of special character that is used to control miniterm (menu), default: %(default)s',
        default=0x14)  # Menu: CTRL+T

    group = parser.add_argument_group('diagnostics')

    group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='suppress non-error messages',
        default=False)

    group.add_argument(
        '--develop',
        action='store_true',
        help='show Python traceback on error',
        default=False)

    args = parser.parse_args()

    if args.menu_char == args.exit_char:
        parser.error('--exit-char can not be the same as --menu-char')

    if args.filter:
        if 'help' in args.filter:
            sys.stderr.write('Available filters:\n')
            sys.stderr.write('\n'.join(
                '{:<10} = {.__doc__}'.format(k, v)
                for k, v in sorted(TRANSFORMATIONS.items())))
            sys.stderr.write('\n')
            sys.exit(1)
        filters = args.filter
    else:
        filters = ['default','send_on_enter']

    while serial_instance is None:
        # no port given on command line -> ask user now
        if args.port is None or args.port == '-':
            try:
                args.port = ask_for_port()
            except KeyboardInterrupt:
                sys.stderr.write('\n')
                parser.error('user aborted and port is not given')
            else:
                if not args.port:
                    parser.error('port is not given')

        stopbits = serial.STOPBITS_ONE_POINT_FIVE if args.stop == 3 else args.stop
        try:
            serial_instance = serial.serial_for_url(
                args.port,
                args.baudrate,
                bytesize=args.data,
                parity=args.parity,
                stopbits=stopbits,
                rtscts=args.rtscts,
                xonxoff=args.xonxoff,
                do_not_open=True)

            if not hasattr(serial_instance, 'cancel_read'):
                # enable timeout for alive flag polling if cancel_read is not available
                serial_instance.timeout = 1

            if args.dtr is not None:
                if not args.quiet:
                    sys.stderr.write('--- forcing DTR {}\n'.format('active' if args.dtr else 'inactive'))
                serial_instance.dtr = args.dtr
            if args.rts is not None:
                if not args.quiet:
                    sys.stderr.write('--- forcing RTS {}\n'.format('active' if args.rts else 'inactive'))
                serial_instance.rts = args.rts

            if isinstance(serial_instance, serial.Serial):
                serial_instance.exclusive = args.exclusive

            serial_instance.open()
        except serial.SerialException as e:
            sys.stderr.write('could not open port {!r}: {}\n'.format(args.port, e))
            if args.develop:
                raise
            if not args.ask:
                sys.exit(1)
            else:
                args.port = '-'
        else:
            break

    rixterm = Terminal(
        serial_instance,
        echo=args.echo,
        eol=args.eol.lower())
        
    rixterm.exit_character = unichr(args.exit_char)
    rixterm.menu_character = unichr(args.menu_char)
    rixterm.raw = args.raw
    rixterm.set_rx_encoding(args.serial_port_encoding)
    rixterm.set_tx_encoding(args.serial_port_encoding)

    load_monitor_filters(args.filter_dir, 'filter_', rixterm, args.quiet)
    flt = SendOnEnter(rixterm)
    miniterm.TRANSFORMATIONS[flt.NAME] = flt

    rixterm.filters=filters
    rixterm.update_transformations()

    if not args.quiet:
        sys.stderr.write('--- Miniterm on {p.name}  {p.baudrate},{p.bytesize},{p.parity},{p.stopbits} ---\n'.format(
            p=rixterm.serial))
        sys.stderr.write('--- Quit: {} | Menu: {} | Help: {} followed by {} ---\n'.format(
            key_description(rixterm.exit_character),
            key_description(rixterm.menu_character),
            key_description(rixterm.menu_character),
            key_description('\x08')))

    rixterm.start()
    try:
        rixterm.join(True)
    except KeyboardInterrupt:
        pass
    if not args.quiet:
        sys.stderr.write('\n--- exit ---\n')
    rixterm.join()
    rixterm.close()
    




# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
    main()
