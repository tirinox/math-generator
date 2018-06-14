import yaml
import os
import util
from collections import namedtuple


class ReaderException(Exception):
    ...


class TemplateReader:
    ClassRef = namedtuple('ClassRef', ['class_name'])
    TextNode = namedtuple('TextNode', ['content'])
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
        return s.startswith('$')

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

    def _parse_var_string(self, var_string: str):
        return [self.TextNode(var_string)]

    def _parse_simple_expression(self, value: str):
        tokens = []
        items = value.split(' ')

        for item in items:
            if self._is_class(item):
                tokens.append(self.ClassRef(item[1:]))
            else:
                tokens.append(self.TextNode(items))
        return self.Expression(tokens)

    def _parse_probablistic_choice_class(self, variants_raw: dict):
        variations = []
        unknown_variations = []

        left_probability = 100.0
        for variant_raw, probability in variants_raw.items():
            probability = str(probability).strip()
            expression = self._parse_simple_expression(variant_raw)

            if probability.endswith('%'):
                prob_number = float(probability[:-1])
                left_probability -= prob_number
                if left_probability < 0.0:
                    raise ReaderException('Total probability > 100% when parsing {}'.format(variants_raw))
                variations.append(self.Variation(expression, prob_number))
            elif probability == 'auto':
                unknown_variations.append(self.Variation(expression, None))
            else:
                raise ReaderException('Cant read probability (use ..% or ~): {}'.format(probability))

        if unknown_variations:
            even_prob = left_probability / len(unknown_variations)
            for variation in unknown_variations:  # type: self.Variation
                variations.append(self.Variation(variation.content, even_prob))

        return self.ProbClass(variations)

    def _parse_class(self, name, value):
        if isinstance(value, str):
            self.classes[name] = self._parse_simple_expression(value)
        elif isinstance(value, dict):
            self.classes[name] = self._parse_probablistic_choice_class(value)
        else:
            raise ReaderException('{}: class\'s values must be dict or str'.format(name))

    def _parse(self):
        for k, v in self._dict_repr.items():
            if self._is_directive(k):
                self._parse_directive(k, v)
            else:
                self._parse_class(k, v)

    def __repr__(self) -> str:
        return "TemplateReader:\nClasses = \n{}\nOpts = \n{}".format(
            util.pretty_print_to_string(self.classes),
            util.pretty_print_to_string(self.options))
