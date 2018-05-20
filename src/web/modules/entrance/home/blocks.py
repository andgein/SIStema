from django.db.models import Q
from django.template.loader import render_to_string
from htmlmin.minify import html_minify

import home.models
from sistema.helpers import nested_query_list

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

        enrolled_to_session_ids = []
        enrolled_to_parallel_ids = []

        status = entrance_models.EntranceStatus.get_visible_status(
            self.school,
            user
        )
        if status is not None and status.is_enrolled:
            sessions_and_parallels = status.sessions_and_parallels

            # If user have selected session and parallel already,
            # then left only this items
            if sessions_and_parallels.filter(selected_by_user=True).exists():
                sessions_and_parallels = sessions_and_parallels.filter(
                    selected_by_user=True
                )

            enrolled_to_session_ids = nested_query_list(
                sessions_and_parallels.values_list('session_id', flat=True)
            )
            enrolled_to_parallel_ids = nested_query_list(
                sessions_and_parallels.values_list('parallel_id', flat=True)
            )
        else:
            # If user is not enrolled, filter out all steps
            # marked as 'visible_only_for_enrolled'
            steps = steps.filter(Q(visible_only_for_enrolled=False))

        # Filter only steps for session and parallel which user has been enrolled in
        # (or steps with no defined session and parallel)
        steps = steps.filter(
            Q(session__isnull=True) | Q(session_id__in=enrolled_to_session_ids))
        steps = steps.filter(
            Q(parallel__isnull=True) | Q(parallel_id__in=enrolled_to_parallel_ids))

        return steps.order_by('order')
