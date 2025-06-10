# messagerie/templatetags/messagerie_filters.py

from django import template

register = template.Library()

@register.filter
def ends_with(value, arg):
    """
    Vérifie si une chaîne de caractères se termine par une sous-chaîne donnée.
    Utilisation: {{ some_string|ends_with:"suffix" }}
    """
    return value.endswith(arg)

@register.filter
def starts_with(value, arg):
    """
    Vérifie si une chaîne de caractères commence par une sous-chaîne donnée.
    Utilisation: {{ some_string|starts_with:"prefix" }}
    """
    return value.startswith(arg)

# Note: Le filtre 'cut' que vous utilisez est un filtre Django intégré.
# Si vous aviez une erreur avec 'cut', il faudrait aussi le vérifier,
# mais il est standard.