from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def replace(value, arg):
    if isinstance(arg, str) and arg.count('|') == 1:
        old, new = arg.split('|')
        return str(value).replace(old, new)
    return value
