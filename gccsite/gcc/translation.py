from modeltranslation.translator import register, TranslationOptions
from gcc.models import Edition


@register(Edition)
class EditionTranslationOptions(TranslationOptions):
    fields = ('long_description',)
