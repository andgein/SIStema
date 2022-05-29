import datetime

from django.conf import settings
from django.db import models, IntegrityError

import polymorphic.models

import schools.models
from sistema.cache import cache


class EntranceLevel(models.Model):
    """
    Уровень вступительной работы.
    Для каждой задачи могут быть указаны уровни, для которых она предназначена.
    Уровень школьника определяется с помощью EntranceLevelLimiter'ов (например,
    на основе тематической анкеты из модуля topics, класса в школе
    или учёбы в других параллелях в прошлые годы)
    """
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='entrance_levels',
    )

    short_name = models.CharField(
        max_length=100,
        help_text='Используется в урлах. '
                  'Лучше обойтись латинскими буквами, цифрами и подчёркиванием'
    )

    name = models.CharField(max_length=100)

    order = models.IntegerField(default=0)

    tasks = models.ManyToManyField(
        'EntranceExamTask',
        blank=True,
        related_name='entrance_levels',
    )

    def __str__(self):
        return 'Уровень «%s» для %s' % (self.name, self.school)

    def __gt__(self, other):
        return self.order > other.order

    def __lt__(self, other):
        return self.order < other.order

    def __ge__(self, other):
        return self.order >= other.order

    def __le__(self, other):
        return self.order <= other.order

    class Meta:
        ordering = ('school_id', 'order')

    MAX_LEVEL_ORDER = 100000000

    @classmethod
    def get_max_entrance_level(cls, school):
        """
        Возвращает специальный «максимальный» уровень, который заведомо больше
        всех существующих. В базе такого уровня нет.
        """
        return cls(
            school=school,
            short_name='max',
            name='Максимальный',
            order=cls.MAX_LEVEL_ORDER
        )

    def is_maximal(self) -> bool:
        return self.order == self.MAX_LEVEL_ORDER


class EntranceLevelOverride(models.Model):
    """
    If present this level is used instead of dynamically computed one.
    """
    school = models.ForeignKey(
        'schools.School',
        on_delete=models.CASCADE,
        related_name='+',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='entrance_level_overrides',
    )

    entrance_level = models.ForeignKey(
        'EntranceLevel',
        on_delete=models.CASCADE,
        related_name='overrides',
    )

    class Meta:
        unique_together = ('school', 'user')

    def __str__(self):
        return 'Уровень {} для {}'.format(self.entrance_level, self.user)

    def save(self, *args, **kwargs):
        if self.school != self.entrance_level.school:
            raise IntegrityError(
                'Entrance level override should belong to the same school as '
                'its entrance level')
        super().save(*args, **kwargs)


class EntranceLevelUpgrade(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    upgraded_to = models.ForeignKey(
        'EntranceLevel',
        on_delete=models.CASCADE,
        related_name='+',
    )

    created_at = models.DateTimeField(auto_now_add=True)


class EntranceLevelUpgradeRequirement(polymorphic.models.PolymorphicModel):
    base_level = models.ForeignKey(
        'EntranceLevel',
        on_delete=models.CASCADE,
        related_name='+',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def is_met_by_user(self, user):
        # Always met by default. Override when subclassing.
        return True


class SolveTaskEntranceLevelUpgradeRequirement(EntranceLevelUpgradeRequirement):
    task = models.ForeignKey(
        'EntranceExamTask',
        on_delete=models.CASCADE,
        related_name='+',
    )

    def is_met_by_user(self, user):
        return self.task.is_solved_by_user(user)


class SelectedEntranceLevel(models.Model):
    school = models.ForeignKey(
        schools.models.School,
        related_name='+',
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='+',
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    level = models.ForeignKey(
        EntranceLevel,
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
    )

    def save(self, *args, **kwargs):
        if self.level.school_id != self.school_id:
            raise IntegrityError(
                'SelectedEntranceLevel: invalid level, should be from school {}'.format(self.school.name)
            )
        super().save(*args, **kwargs)


class EntranceLevelLimiter(polymorphic.models.PolymorphicModel):
    school = models.ForeignKey(
        schools.models.School,
        related_name='entrance_level_limiters',
        on_delete=models.CASCADE,
    )

    is_recommendation_only_limiter = models.BooleanField(
        default=False, help_text="Если True, то лимитер на самом деле не участвует в ограничении "
                                 "доступных уровней, а влияет только на показ «рекомендуемого» уровня"
    )

    def _find_minimal_level(self):
        return EntranceLevel.objects.filter(school=self.school).order_by('order').first()

    def get_limit(self, user):
        raise NotImplementedError(
            '%s should implement get_limit()' % (self.__class__.__name__, )
        )


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
    def __str__(self):
        return 'Лимитер по прошлым посещениям школы'

    @cache(60)
    def _cached_limits_for_parallels(self):
        return list(self.limits_for_parallels.all())

    def _limits_for_parallels_filter(self, key: str, value_list: list):
        return [item for item in self._cached_limits_for_parallels() if getattr(item, key) in value_list]

    def get_limit(self, user):
        current_limit = EntranceLevelLimit(self._find_minimal_level())

        # First, find limits for specific parallel in specific school
        user_parallel_ids = list(
            user.school_participations.values_list('parallel_id', flat=True)
        )
        for limit_by_parallel in self._limits_for_parallels_filter(
            'previous_parallel_id', user_parallel_ids
        ):
            current_limit.update_with_other(
                EntranceLevelLimit(limit_by_parallel.level)
            )

        # Second, find limits for parallel by its short name
        user_parallel_short_names = list(
            user.school_participations.values_list('parallel__short_name', flat=True)
        )
        for limit_by_parallel_short_name in self._limits_for_parallels_filter(
            'previous_parallel_short_name', user_parallel_short_names
        ):
            current_limit.update_with_other(
                EntranceLevelLimit(limit_by_parallel_short_name.level)
            )

        return current_limit


class AlreadyWasEntranceLevelLimiterForParallel(models.Model):
    limiter = models.ForeignKey(
        AlreadyWasEntranceLevelLimiter,
        on_delete=models.CASCADE,
        related_name='limits_for_parallels',
    )

    previous_parallel_short_name = models.CharField(
        max_length=100,
        help_text='short_name параллели, в которой был школьник. '
                  'Укажите это поле или previous_parallel.',
        blank=True,
        default=''
    )

    previous_parallel = models.ForeignKey(
        schools.models.Parallel,
        on_delete=models.CASCADE,
        related_name='+',
        blank=True,
        null=True,
        default=None,
        help_text='Параллель, в которой был школьник. Укажите это поле или previous_parallel_short_name',
    )

    level = models.ForeignKey(
        EntranceLevel,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Какой уровень вступительной для такого школьника будет минимальным'
    )

    def __str__(self):
        return 'Бывшие в параллели {} получают работу уровня {}'.format(
            self.previous_parallel_short_name if self.previous_parallel is None
            else self.previous_parallel.name,
            self.level.name,
        )

    class Meta:
        unique_together = (
            ('limiter', 'previous_parallel'),
        )


class AgeEntranceLevelLimiter(EntranceLevelLimiter):
    def __str__(self):
        return 'Лимитер по классу'

    def get_limit(self, user):
        if not hasattr(user, 'profile'):
            return EntranceLevelLimit(self._find_minimal_level())

        # Let's try to find out class in the right year
        if self.school.sessions.exists():
            date = self.school.sessions.first().start_date
        elif self.school.year:
            try:
                date = datetime.date(year=int(self.school.year), month=1, day=1)
            except ValueError:
                date = None
        else:
            date = None

        current_class = user.profile.get_class(date=date)
        if current_class is None:
            return EntranceLevelLimit(self._find_minimal_level())

        limit = (
            self.limits_for_classes
                .filter(current_class__lte=current_class)
                .order_by('-current_class')
                .first()
        )
        if limit is not None:
            return EntranceLevelLimit(limit.level)

        return EntranceLevelLimit(self._find_minimal_level())


class AgeEntranceLevelLimiterForClass(models.Model):
    limiter = models.ForeignKey(
        AgeEntranceLevelLimiter,
        on_delete=models.CASCADE,
        related_name='limits_for_classes',
    )

    current_class = models.IntegerField(
        help_text='Текущий класс школьника (например, '
                  'если тут указан 8 класс, то уровень будет применяться как '
                  'ограничения для всех, кто в 8 классе и старше)',
    )

    level = models.ForeignKey(
        EntranceLevel,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='Какой уровень вступительной для такого школьника будет минимальным'
    )

    def __str__(self):
        return 'Поступающие из {} класса и старше получают работу уровня {}'.format(
            self.current_class, self.level.name
        )


class EnrollmentTypeEntranceLevelLimiter(EntranceLevelLimiter):
    def __str__(self):
        return 'Лимитер по авто-поступлению'

    def get_limit(self, user):
        # It's here to avoid cyclic imports
        from modules.entrance.models.steps import SelectedEnrollmentType
        selected_enrollment_types = list(SelectedEnrollmentType.objects.filter(
            user=user,
            step__school=self.school
        ))

        current_limit = EntranceLevelLimit(None)
        for selected_enrollment_type in selected_enrollment_types:
            if (selected_enrollment_type.is_moderated and
               selected_enrollment_type.is_approved and
               selected_enrollment_type.has_entrance_level()):
                entrance_level = selected_enrollment_type.get_entrance_level()
                current_limit.update_with_other(EntranceLevelLimit(entrance_level))

        return current_limit
