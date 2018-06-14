from reader import TemplateReader
import util


r = TemplateReader('templates/example.yaml')

for class_name, class_data in r.classes.items():
    print('-'*50 + ' ' + class_name + ' ' + '-'*50)
    print(util.pretty_print_to_string(class_data))
    print()


# r = TemplateReader('templates/null.yaml')
# print(r._parse_range('1-5'))