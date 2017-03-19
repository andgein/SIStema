from django.db.models import Q
from django.template.loader import render_to_string
from htmlmin.minify import html_minify

import home.models

__all__ = ['EntranceStepsHomePageBlock']


class EntranceStepsHomePageBlock(home.models.AbstractHomePageBlock):
    ENTRANCE_STEPS_TEMPLATES_FOLDER = 'entrance/steps'

    css_files = ['entrance/css/timeline.css']
    js_files = ['entrance/js/timeline.js']

    def build(self, request):
        # It's here to avoid cyclic imports
        import modules.entrance.models as entrance_models

        steps = self._get_entrance_steps_for_user(request.user)

        blocks = []
        for step in steps:
            block = step.build(request.user)

            if block is not None:
                template_file = '%s/%s' % (self.ENTRANCE_STEPS_TEMPLATES_FOLDER,
                                           step.template_file)
                rendered_block = render_to_string(template_file, {
                    'entrance_block': block,
                    'EntranceStepState': entrance_models.EntranceStepState
                })

                # Minifying rendered block by removing spaces and newlines.
                # Use 'html.parser' instead of 'html5lib' because html5lib adds
                # DOCTYPE, <html> and <body> tags to the output
                rendered_block = html_minify(
                    rendered_block,
                    parser='html.parser'
                )

                blocks.append(rendered_block)

        self.blocks = blocks

    def _get_entrance_steps_for_user(self, user):
        # It's here to avoid cyclic imports
        import modules.entrance.models as entrance_models

        status = entrance_models.EntranceStatus.get_visible_status(
            self.school,
            user
        )
        entranced_session = None if status is None else status.session
        entranced_parallel = None if status is None else status.parallel
        steps = entrance_models.AbstractEntranceStep.objects.filter(
            school=self.school
        )
        # Filter only steps for these session and parallel
        # (or steps with no defined session and parallel)
        steps = steps.filter(
            Q(session__isnull=True) | Q(session=entranced_session))
        steps = steps.filter(
            Q(parallel__isnull=True) | Q(parallel=entranced_parallel))

        # If user is not enrolled, filter out all steps
        # marked as 'visible_only_for_enrolled'
        if status is None or not status.is_enrolled:
            steps = steps.filter(Q(visible_only_for_enrolled=False))

        return steps
