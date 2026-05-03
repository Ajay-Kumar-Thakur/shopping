from django import template

register = template.Library()

FLAG_MAP = {
    'en':      '🇬🇧',
    'ne':      '🇳🇵',
    'hi':      '🇮🇳',
    'zh-hans': '🇨🇳',
    'ar':      '🇸🇦',
    'fr':      '🇫🇷',
    'de':      '🇩🇪',
    'es':      '🇪🇸',
    'ja':      '🇯🇵',
    'ko':      '🇰🇷',
    'pt':      '🇧🇷',
    'ru':      '🇷🇺',
}


@register.filter(name='language_flag')
def language_flag(lang_code):
    """Return a flag emoji for the given language code."""
    return FLAG_MAP.get(lang_code, '🌐')