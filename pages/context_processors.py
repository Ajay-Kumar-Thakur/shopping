from django.conf import settings


def lang_info(request):
    """
    Injects LANG_INFO_LIST and CURRENT_LANG into every template context.
    Add 'pages.context_processors.lang_info' to TEMPLATES > OPTIONS > context_processors
    in settings.py
    """
    from django.utils.translation import get_language

    langs = [
        {'code': code, 'name_local': name}
        for code, name in settings.LANGUAGES
    ]

    return {
        'LANG_INFO_LIST': langs,
        'CURRENT_LANG': get_language() or settings.LANGUAGE_CODE.split('-')[0],
    }