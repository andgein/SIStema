from django.db.models import Q
from django.template.loader import render_to_string
from htmlmin.minify import html_minify

import home.models

__all__ = ['EntranceStepsHomePageBlock']


class EntranceStepsHomePageBlock(home.models.AbstractHomePageBlock):
    ENTRANCE_STEPS_TEMPLATES_FOLDER = 'entrance/steps'

    css_files = ['entrance/css/timeline.css',
                 'entrance/css/timeline-sm.css']
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
                }, request=request)

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

        steps = self.school.entrance_steps.all()

        enrolled_to_session = None
        enrolled_to_parallel = None

        status = entrance_models.EntranceStatus.get_visible_status(
            self.school,
            user
        )
        if status is not None and status.is_enrolled:
            enrolled_to_session = status.session
            enrolled_to_parallel = status.parallel
        else:
            # If user is not enrolled, filter out all steps
            # marked as 'visible_only_for_enrolled'
            steps = steps.filter(Q(visible_only_for_enrolled=False))

        # Filter only steps for session and parallel which user has been enrolled in
        # (or steps with no defined session and parallel)
        steps = steps.filter(
            Q(session__isnull=True) | Q(session=enrolled_to_session))
        steps = steps.filter(
            Q(parallel__isnull=True) | Q(parallel=enrolled_to_parallel))

        return steps.order_by('order')
