from django.template.loader import render_to_string

import home.models

__all__ = ['EntranceStepsHomePageBlock']


class EntranceStepsHomePageBlock(home.models.AbstractHomePageBlock):
    ENTRANCE_STEPS_TEMPLATES_FOLDER = 'entrance/steps'

    css_files = ['entrance/css/timeline.css']
    js_files = ['entrance/js/timeline.js']

    def build(self, request):
        # It's here to avoid cyclic imports
        from modules.entrance.models import steps as entrance_steps

        steps = (entrance_steps.AbstractEntranceStep.objects.
                 filter(school=request.school))

        blocks = []
        for step in steps:
            block = step.build(request.user)

            if block is not None:
                # TODO(andgein): May be replace with {% include %} in template?
                template_file = '%s/%s' % (self.ENTRANCE_STEPS_TEMPLATES_FOLDER,
                                           step.template_file)
                rendered_block = render_to_string(template_file, {
                    'entrance_block': block,
                    'EntranceStepState': entrance_steps.EntranceStepState
                })

                blocks.append(rendered_block)

        self.blocks = blocks
