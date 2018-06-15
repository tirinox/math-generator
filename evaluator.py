from reader import TemplateReader
import random
import util


class TemplateEvaluator:
    def __init__(self, reader: TemplateReader, rng: random.Random = None):
        self._reader = reader
        self._random = rng or random.Random(reader.get_seed())

    def _eval(self, expr):
        if isinstance(expr, str):
            return expr
        elif isinstance(expr, TemplateReader.ProbClass):
            variations = expr.variations
            values, probs = [], []
            for v in variations:  # type: TemplateReader.Variation
                values.append(v.content)
                probs.append(v.probability)

            choice = self._random.choices(values, weights=probs)[0]

            return self._eval(choice)
        elif isinstance(expr, TemplateReader.Expression):
            tokens = expr.tokens

            generated_sequence = []

            for token in tokens:
                if isinstance(token, str):
                    generated_sequence.append(token)
                elif isinstance(token, TemplateReader.ClassRef):
                    class_name = token.class_name
                    generated_sequence.append(self.eval_class(class_name))

            return generated_sequence

    def eval_class(self, class_name, flat=True):
        class_data = self._reader.classes[class_name]
        result = self._eval(class_data)
        return util.flatten(result) if flat else result