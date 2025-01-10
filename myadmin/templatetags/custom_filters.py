from django import template

register = template.Library()

@register.filter
def remaining_range(current_length):
    """Returns range for remaining slots up to 4"""
    return range(current_length, 4)