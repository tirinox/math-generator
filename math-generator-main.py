from reader import TemplateReader
from evaluator import TemplateEvaluator

r = TemplateReader('templates/example.yaml')
# r.print()
# print()
# print('-~'*100)
# print()

from random import Random

rng = Random()
ev = TemplateEvaluator(r, rng)

from collections import Counter

xx = []

for c in ['eqs']:
    for i in range(15):
        r = ev.eval_class(c)
        # print(r)
        print(''.join(r))
        xx.append(r)

# print(Counter(xx))


# r = TemplateReader('templates/null.yaml')
# print(r._parse_range('1-5'))