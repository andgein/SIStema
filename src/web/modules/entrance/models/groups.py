from sqlite3 import IntegrityError

from django.db import models
from django.db.models import Q

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
                  'Отказавшиеся от участия в любом случае не попадают в группу'
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


class EnrolledUsersGroup(groups.models.AbstractGroup):
    """
        Group for enrolled (maybe to some specific session or parallel) users.
        Users who rejected their participation are not included in this group.
    """
    session = models.ForeignKey(
        'schools.Session',
        related_name='+',
        on_delete=models.CASCADE,
        null=True,
        default=None,
        blank=True,
    )

    parallel = models.ForeignKey(
        'schools.Parallel',
        related_name='+',
        on_delete=models.CASCADE,
        null=True,
        default=None,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.session is not None and self.session.school_id != self.school_id:
            raise IntegrityError('%s: session should belong to the same school, but %s != %s' % (
                self.__class__.__name__,
                self.session.school,
                self.school
            ))
        if self.parallel is not None and self.parallel.school_id != self.school_id:
            raise IntegrityError('%s: parallel should belong to the same school, but %s != %s' % (
                self.__class__.__name__,
                self.parallel.school,
                self.school
            ))
        if (self.session is not None and
            self.parallel is not None and
            not self.parallel.sessions.filter(id=self.session_id).exists()):
            raise IntegrityError('%s: parallel %s doesn\'t exist in session %s' % (
                self.__class__.__name__,
                self.parallel,
                self.school
            ))
        super().save(*args, **kwargs)

    def is_user_in_group(self, user):
        status = EntranceStatus.get_visible_status(self.school, user)
        if status is None or not status.is_enrolled:
            return False

        qs = status.sessions_and_parallels.all()
        if status.is_approved:
            qs = qs.filter(selected_by_user=True)

        if self.session is not None:
            qs = qs.filter(session=self.session)
        if self.parallel is not None:
            qs = qs.filter(parallel=self.parallel)

        if not qs.exists():
            return False

        # User is not included in the group if there is an absence reason for him
        if AbstractAbsenceReason.objects.filter(school=self.school, user=user).exists():
            return False

        return True

    @property
    def user_ids(self):
        qs = EntranceStatus.objects.filter(
            school=self.school,
            status=EntranceStatus.Status.ENROLLED,
            is_status_visible=True
        )
        if self.session is not None and self.parallel is None:
            # Filter users who approved this session or who not approved participation yet
            qs = qs.filter(
                Q(
                    sessions_and_parallels__selected_by_user=True,
                    sessions_and_parallels__session=self.session
                ) | Q(
                    is_approved=False,
                    sessions_and_parallels__session=self.session
                )
            )
        if self.parallel is not None and self.session is None:
            qs = qs.filter(
                Q(
                    sessions_and_parallels__selected_by_user=True,
                    sessions_and_parallels__parallel=self.parallel
                ) | Q(
                    is_approved=False,
                    sessions_and_parallels__parallel=self.parallel
                )
            )
        if self.session is not None and self.parallel is not None:
            qs = qs.filter(
                Q(
                    sessions_and_parallels__selected_by_user=True,
                    sessions_and_parallels__session=self.session,
                    sessions_and_parallels__parallel=self.parallel
                ) | Q(
                    is_approved=False,
                    sessions_and_parallels__session=self.session,
                    sessions_and_parallels__parallel=self.parallel
                )
            )

        enrolled_user_ids = qs.values_list('user_id', flat=True)

        absence_user_ids = AbstractAbsenceReason.objects.filter(
            school=self.school,
        ).values_list('user_id', flat=True)

        return set(enrolled_user_ids) - set(absence_user_ids)
