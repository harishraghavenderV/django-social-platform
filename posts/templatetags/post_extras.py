import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key in templates."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def social_text(value):
    text = escape(value or '')

    def replace_token(match):
        token = match.group(0)
        if token.startswith('@'):
            username = token[1:]
            return f'<a class="social-token" href="/profile/{username}/">{token}</a>'
        tag = token[1:].lower()
        return f'<a class="social-token" href="/hashtag/{tag}/">{token}</a>'

    linked = re.sub(r'(?<![\w/])[@#][A-Za-z0-9_]+', replace_token, text)
    return mark_safe(linked)
