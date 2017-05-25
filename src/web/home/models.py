from django.db import models
import polymorphic.models

import schools.models


class AbstractHomePageBlock(polymorphic.models.PolymorphicModel):
    school = models.ForeignKey(
        schools.models.School, related_name='home_page_blocks'
    )

    order = models.PositiveIntegerField(
        help_text='Блоки показываются в порядке возрастания этого параметра'
    )

    # Override it in subclass to include some css files for your block
    css_files = []

    # Override it in subclass to include some js files for your block
    js_files = []

    class Meta:
        verbose_name = 'home page block'

    def build(self, request):
        raise NotImplementedError()
