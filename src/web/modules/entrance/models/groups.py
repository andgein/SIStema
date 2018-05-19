from django.db import models

import groups.models
from .main import EntranceStatus, AbstractAbsenceReason


class EntranceStatusGroup(groups.models.AbstractGroup):
    status = models.IntegerField(
        choices=EntranceStatus.Status.choices,
        validators=[EntranceStatus.Status.validator]
    )

    def is_user_in_group(self, user):
        return EntranceStatus.objects.filter(
            user=user,
            status=self.status,
            school=self.school,
        ).exists()

    @property
    def user_ids(self):
        return EntranceStatus.objects.filter(
            status=self.status,
            school=self.school
        ).values_list('user_id', flat=True)


class EnrollmentApprovingStatusGroup(groups.models.AbstractGroup):
    is_approved = models.BooleanField(
        help_text='Поместить в группу тех, кто подтвердил участие, или тех, кто не подтвердил? '
                  'Отказавщиеся от участия в любом случае не попадают в группу'
    )

    def is_user_in_group(self, user):
        entrance_status = EntranceStatus.get_visible_status(self.school, user)
        absence_reason = AbstractAbsenceReason.for_user_in_school(self.school, user)
        return (entrance_status is not None and
                entrance_status.is_enrolled and
                entrance_status.is_approved == self.is_approved and
                absence_reason is None)

    @property
    def user_ids(self):
        approved_user_ids = EntranceStatus.objects.filter(
            school=self.school,
            status=EntranceStatus.Status.ENROLLED,
            is_status_visible=True,
            is_approved=self.is_approved,
        ).values_list('user_id', flat=True)

        absence_user_ids = AbstractAbsenceReason.objects.filter(
            school=self.school,
        ).values_list('user_id', flat=True)

        return set(approved_user_ids) - set(absence_user_ids)
