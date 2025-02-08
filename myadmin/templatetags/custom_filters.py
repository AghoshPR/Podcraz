from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def remaining_range(current_length):
    """Returns range for remaining slots up to 4"""
    return range(current_length, 4)

@register.filter
def multiply(value, arg):
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return 0
    
@register.filter
def subtract(value, arg):
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def absolute(value):
    try:
        return abs(Decimal(str(value)))
    except (ValueError, TypeError, InvalidOperation):
        return 0