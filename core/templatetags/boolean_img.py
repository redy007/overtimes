from django import template

register = template.Library()

@register.inclusion_tag('includes/boolean_flag_img.html')
def boolean_img(flag):
    return {'flag': flag}
