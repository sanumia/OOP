from django import template

register = template.Library()

@register.filter(name='sub')  # Explicitly set the filter name
def sub(value, arg):
    """Subtracts the arg from the value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return value 