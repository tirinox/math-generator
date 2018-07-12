from collections import namedtuple

Annotation = namedtuple('Annotation', ['label', 'x', 'y', 'w', 'h'])
Sample = namedtuple('Sample', ['image', 'annotations'])


class ImageGenerator:
    def generate(self, tokens: []) -> Sample:
        return Sample(None, [])