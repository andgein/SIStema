from django.db.models import Q
import django.contrib.admin.views.decorators as admin_decorators
import django.utils.decorators as utils_decorators

from dal import autocomplete

from modules.ejudge import models


@utils_decorators.method_decorator(admin_decorators.staff_member_required,
                                   name='dispatch')
class SolutionCheckingResultAutocomplete(autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        super().__init__(model=models.SolutionCheckingResult, **kwargs)

    def get_queryset(self):
        if not self.q.isdigit():
            return models.SolutionCheckingResult.objects.none()

        return models.SolutionCheckingResult.objects.filter(id=int(self.q))


@utils_decorators.method_decorator(admin_decorators.staff_member_required,
                                   name='dispatch')
class SubmissionAutocomplete(autocomplete.Select2QuerySetView):
    def __init__(self, **kwargs):
        super().__init__(model=models.Submission, **kwargs)

    def get_queryset(self):
        if not self.q.isdigit():
            return models.Submission.objects.none()

        return models.Submission.objects.filter(ejudge_submit_id=int(self.q))
