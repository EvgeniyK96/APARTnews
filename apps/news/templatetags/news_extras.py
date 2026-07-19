from django import template

from .. import services

register = template.Library()


@register.filter
def category_label(slug):
    return services.category_label(slug or "")
