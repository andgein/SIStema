import datetime

from . import models


class EntranceLevelLimiter:
    def __init__(self, school):
        self.school = school

    def _find_minimal_level(self):
        return models.EntranceLevel.objects.filter(school=self.school).order_by('order').first()

    def get_limit(self, user):
        raise NotImplementedError('modules.entrance.levels.EntranceLevelLimiter: Child must implement get_limit()')


class EntranceLevelLimit:
    def __init__(self, min_level):
        self.min_level = min_level

    def update_with_other(self, other_limit):
        if self.min_level is None:
            self.min_level = other_limit.min_level
            return

        if other_limit.min_level is not None:
            if self.min_level < other_limit.min_level:
                self.min_level = other_limit.min_level


class AlreadyWasEntranceLevelLimiter(EntranceLevelLimiter):
    # TODO: move it to settings?
    limit_for_parallel = {
        'a': 'a',
        'a0': 'a',
        'a_ml': 'a',
        'a_prime': 'a',
        'aa': 'a',
        'as': 'a',
        'ay': 'a',
        'b': 'a_prime',
        'b_prime': 'b',
        'c': 'b_prime',
        'c.cpp': 'b_prime',
        'c.python': 'b_prime',
        'c_prime': 'c',
        'd': 'c_prime',
    }

    def get_limit(self, user):
        levels = models.EntranceLevel.objects.filter(school=self.school)
        limit = EntranceLevelLimit(self._find_minimal_level())
        for participation in user.school_participations.all():
            limit_short_name = self.limit_for_parallel.get(
                participation.parallel.short_name)
            if limit_short_name is not None:
                limit_level = levels.get(short_name=limit_short_name)
                limit.update_with_other(EntranceLevelLimit(limit_level))

        return limit


class AgeEntranceLevelLimiter(EntranceLevelLimiter):
    def get_limit(self, user):
        if not hasattr(user, 'profile'):
            return EntranceLevelLimit(self._find_minimal_level())

        # Let's try to find out class in the right year
        if self.school.sessions.exists():
            date = self.school.sessions.first().start_date
        elif self.school.year:
            date = datetime.date(year=self.school.year, month=1, day=1)
        else:
            date = None

        current_class = user.profile.get_class(date=date)
        if current_class is None:
            return EntranceLevelLimit(self._find_minimal_level())

        levels = models.EntranceLevel.objects.filter(school=self.school)

        if current_class >= 10:
            return EntranceLevelLimit(levels.filter(short_name='b_prime').get())
        if current_class == 9:
            return EntranceLevelLimit(levels.filter(short_name='c').get())
        if current_class == 8:
            return EntranceLevelLimit(levels.filter(short_name='c_prime').get())

        return EntranceLevelLimit(self._find_minimal_level())


class EnrollmentTypeEntranceLevelLimiter(EntranceLevelLimiter):
    def get_limit(self, user):
        selected_enrollment_types = list(models.SelectedEnrollmentType.objects.filter(
            user=user,
            step__school=self.school
        ))

        current_limit = EntranceLevelLimit(None)
        for selected_enrollment_type in selected_enrollment_types:
            if (selected_enrollment_type.is_moderated and
               selected_enrollment_type.is_approved and
               selected_enrollment_type.entrance_level is not None):
                current_limit.update_with_other(
                    EntranceLevelLimit(selected_enrollment_type.entrance_level)
                )

        return current_limit
