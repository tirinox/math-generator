import pprint

_pp = pprint.PrettyPrinter(indent=4)


def pretty_print_to_string(x):
    return _pp.pformat(x)


def flatten(S):
    if not S:
        return S
    if isinstance(S[0], list):
        return flatten(S[0]) + flatten(S[1:])
    return S[:1] + flatten(S[1:])
