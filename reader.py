import yaml
import os
import util
from collections import namedtuple


class ReaderException(Exception):
    ...


class TemplateReader:
    ClassRef = namedtuple('ClassRef', ['class_name'])
    Expression = namedtuple('Expression', ['tokens'])
    ProbClass = namedtuple('ProbClass', ['variations'])
    Variation = namedtuple('Variation', ['content', 'probability'])

    def __init__(self, file_name, current_path=None, recc_level=0):
        if recc_level is 10:
            raise ReaderException('Too recursive includes')

        self._recc_level = recc_level

        with open(file_name, 'r') as stream:
            self._dict_repr = yaml.load(stream)

        if current_path:
            self._current_path = current_path
        else:
            self._current_path = os.path.dirname(os.path.abspath(file_name))

        self.classes = {}
        self.options = {}

        if self._dict_repr:
            self._parse()

    @staticmethod
    def _is_class(s: str):
        return s.startswith('$') and len(s) > 1

    @staticmethod
    def _is_directive(s: str):
        return s.startswith('^')

    def _search_for_include(self, original_file_name):
        if os.path.isfile(original_file_name):
            return original_file_name
        else:
            other_file_name = os.path.join(self._current_path, original_file_name)
            if os.path.isfile(other_file_name):
                return other_file_name
        return None

    def _do_include(self, included_file_name):
        included_file_name_new = self._search_for_include(included_file_name)
        if not included_file_name_new:
            raise FileNotFoundError('include was not found: {}'.format(included_file_name))

        reader = TemplateReader(included_file_name_new, self._current_path, self._recc_level + 1)

        self.classes.update(reader.classes)
        self.options.update(reader.options)

    def _parse_directive(self, name, value):
        if name == '^include':
            if isinstance(value, str):
                value = [value]
            for file_name in value:
                self._do_include(file_name)
        else:
            self.options[name] = value

    def _parse_range(self, range_str: str):
        def syntax_error(extra=''):
            raise ReaderException('syntax error "{}" in {}'.format(extra, range_str))

        if range_str == '\\' or range_str == '-':
            return range_str

        result_chars = set()
        position = 0
        total_len = len(range_str)

        def want_next(p):
            p += 1
            if p >= total_len:
                syntax_error('unexpected end')
            return p, range_str[p]

        def want_prev(p):
            if p <= 0:
                syntax_error('no symbol before')
            return range_str[p - 1]

        while position < total_len:
            symbol = range_str[position]
            if symbol == '\\':
                position, next_symbol = want_next(position)
                result_chars.add(next_symbol)
            elif symbol == '-':
                range_start = want_prev(position)
                position, range_end = want_next(position)
                for symbol_index in range(ord(range_start), ord(range_end) + 1):
                    result_chars.add(chr(symbol_index))
            else:
                result_chars.add(symbol)
            position += 1

        return list(result_chars)

    def _parse_simple_expression(self, value: str, allow_ranges):
        tokens = []
        value = str(value).strip()
        items = value.split(' ')

        if allow_ranges and len(items) == 1 and not self._is_class(value):
            return self._parse_range(value)
        else:
            for item in items:
                if self._is_class(item):
                    tokens.append(self.ClassRef(item[1:]))
                else:
                    tokens.append(item)

            if len(tokens) == 1 and isinstance(tokens[0], str):
                return tokens[0]
            else:
                return self.Expression(tokens)

    def _parse_probablistic_choice_class(self, variants_raw: dict):
        variations = []
        unknown_variations = []

        left_probability = 100.0
        for variant_raw, probability in variants_raw.items():
            probability = str(probability).strip()

            result = self._parse_simple_expression(variant_raw, allow_ranges=True)
            many_results = isinstance(result, list)

            if probability.endswith('%'):
                prob_number = float(probability[:-1])
                left_probability -= prob_number
                if left_probability < 0.0:
                    raise ReaderException('Total probability > 100% when parsing {}'.format(variants_raw))

                if many_results:
                    n = len(result)
                    each_prod_number = prob_number / n
                    variations += list(self.Variation(r, each_prod_number) for r in result)
                else:
                    variations.append(self.Variation(result, prob_number))
            elif probability == 'auto':
                if many_results:
                    unknown_variations += list(self.Variation(r, None) for r in result)
                else:
                    unknown_variations.append(self.Variation(result, None))
            else:
                raise ReaderException('Cant read probability (use ..% or ~): {}'.format(probability))

        if unknown_variations:
            even_prob = left_probability / len(unknown_variations)
            for variation in unknown_variations:  # type: self.Variation
                variations.append(self.Variation(variation.content, even_prob))

        return self.ProbClass(variations)

    def _parse_class(self, name, value):
        if isinstance(value, str):
            self.classes[name] = self._parse_simple_expression(value, allow_ranges=False)
        elif isinstance(value, dict):
            self.classes[name] = self._parse_probablistic_choice_class(value)
        elif isinstance(value, list):
            self.classes[name] = self._parse_probablistic_choice_class({x:'auto' for x in value})
        else:
            raise ReaderException('{}: invalid class content'.format(name))

    def _parse(self):
        for k, v in self._dict_repr.items():
            if self._is_directive(k):
                self._parse_directive(k, v)
            else:
                self._parse_class(k, v)
        self._check_classes(self.classes)

    def _check_classes(self, coll):
        if isinstance(coll, self.ClassRef):
            if coll.class_name not in self.classes:
                raise ReaderException('undefined class {}'.format(coll.class_name))
        elif isinstance(coll, dict):
            for v in coll.values():
                self._check_classes(v)
        elif isinstance(coll, (list, tuple)):
            for v in coll:
                self._check_classes(v)

    def __repr__(self) -> str:
        return "TemplateReader:\nClasses = \n{}\nOpts = \n{}".format(
            util.pretty_print_to_string(self.classes),
            util.pretty_print_to_string(self.options))

    def print(self):
        for class_name, class_data in self.classes.items():
            print('-' * 50 + ' ' + class_name + ' ' + '-' * 50)
            print(util.pretty_print_to_string(class_data))
            print()

