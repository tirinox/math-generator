import pprint

_pp = pprint.PrettyPrinter(indent=4)


def pretty_print_to_string(x):
    return _pp.pformat(x)