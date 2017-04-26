from django.db.models import Q

from users import models
from modules.entrance import models as entrance_models

import operator


__en2ru_char_map = {
    'a': 'а',
    'b': 'б',
    'с': 'к',
    'd': 'д',
    'e': 'е',
    'f': 'ф',
    'g': 'г',
    'h': 'х',
    'i': 'и',
    'j': 'й',
    'k': 'к',
    'l': 'л',
    'm': 'м',
    'n': 'н',
    'o': 'о',
    'p': 'п',
    'r': 'р',
    's': 'с',
    't': 'т',
    'u': 'у',
    'v': 'в',
    'x': 'кс',
    'y': 'ы',
    'z': 'з',
}


def _up_word(word):
    return word[0].upper() + word[1:]


def _translit_en2ru(s):
    if s.endswith('iy'):
        s = s[:-2] + 'ий'
    if s.endswith('y'):
        s = s[:-1] + 'ий'
    for a, b in [('sch', 'щ'), ('sh', 'ш'), ('zh', 'ж'), ('сh', 'ч'),
                 ('kh', 'х'), ('ya', 'я'), ('yo', 'ё'), ('yu', 'ю')]:
        s = s.replace(a, b)
        s = s.replace(_up_word(a), _up_word(b))
    t = ''
    for ch in list(s):
        ch2 = ch.lower()
        if ch in __en2ru_char_map:
            t += __en2ru_char_map[ch]
        elif ch2 in __en2ru_char_map:
            t += _up_word(__en2ru_char_map[ch2])
        else:
            t += ch
    return t


__first_name_normalization_dict = {
    'саша': 'александр',
    'александра': 'александр',
    'шура': 'александр',
    'женя': 'евгений',
    'евгения': 'евгений',
    'валя': 'валентин',
    'валентина': 'валентин',
    'катя': 'екатерина',
    'костя': 'константин',
    'коля': 'николай',
    'леша': 'алексей',
    'рома': 'роман',
    'маша': 'мария',
    'миша': 'михаил',
    'вадик': 'вадим',
    'вова': 'владимир',
    'сеня': 'арсений',
    'паша': 'павел',
    'сережа': 'сергей',
    'петя': 'петр',
    'толя': 'анатолий',
    'дима': 'дмитрий',
    'степа': 'степан',
    'жора': 'георгий',
    'гоша': 'георгий',
    'ваня': 'иван',
    'виталик': 'виталий',
    'данил': 'даниил',
    'соня': 'софия',
    'софья': 'софия',
    'ира': 'ирина',
    'юля': 'юлия',
    'влад': 'владислав',
    'влада': 'владислава',
    'стас': 'станислав',
    'ярик': 'ярослав',
    'тема': 'артем',
    'артемий': 'артем',
    'галя': 'галина',
    'ксюша': 'ксения',
    'леня': 'леонид',
    'лена': 'елена',
    'боря': 'борис',
    'тоша': 'антон',
    'федя': 'федор',
    'таня': 'татьяна',
    'макс': 'максим',
    'аня': 'анна',
    'вася': 'василий',
    'валера': 'валерий',
    'даша': 'дарья',
    'юра': 'юрий',
    'настя': 'анастасия',
    'оля': 'ольга',
    'наташа': 'наталья',
    'наталия': 'наталья',
    'света': 'светлана',
    'витя': 'виктор',
    'гриша': 'григорий',
    'рита': 'маргарита',
    'лиза': 'елизавета',
    'лида': 'лидия',
    'люба': 'любовь',
    'варя': 'варвара',
    'тима': 'тимофей',
    'веня': 'вениамин',
    'сева': 'всеволод',
    'уля': 'ульяна',
    'эдик': 'эдуард',
}


_no_break_space = b'\xc2\xa0'.decode('utf8')


def _normalize(s):
    if not s:
        return s
    s = _translit_en2ru(s)
    s = s.lower()
    s = s.replace('ё', 'е')
    s = s.replace(_no_break_space, ' ')
    return s


def _normalize_first_name(first_name):
    if not first_name:
        return first_name
    first_name = _normalize(first_name)
    return __first_name_normalization_dict.get(first_name, first_name)


def _match_names(name1, name2, can_be_null):
    if not name1 or not name2:
        return can_be_null
    return _normalize(name1) == _normalize(name2)


def match_first_names(name1, name2):
    name1 = _normalize_first_name(name1)
    name2 = _normalize_first_name(name2)
    return _match_names(name1, name2, True)


def match_middle_names(name1, name2):
    return _match_names(name1, name2, True)


def match_last_names(name1, name2):
    return _match_names(name1, name2, False)


class SimilarAccountSearcher(object):
    def __init__(self, new_user_profile):
        self._new_user_profile = new_user_profile
        self._candidates = []

    def search(self, strict=True):
        poldnev_person = self._new_user_profile.poldnev_person
        if poldnev_person:
            if poldnev_person.user:
                return [poldnev_person.user]
            related_profiles = poldnev_person.user_profiles.all()
            if related_profiles:
                return map(operator.attrgetter('user'), related_profiles)

        last_name = self._new_user_profile.last_name
        if not last_name:
            return []

        first_name = self._new_user_profile.first_name
        birth_date = self._new_user_profile.birth_date

        expr = Q(last_name=last_name) | Q(profile__last_name=last_name) | Q(poldnev_person__last_name=last_name)
        if birth_date:
            expr |= Q(profile__birth_date=birth_date)
        self._candidates = list(models.User.objects
                                .select_related('profile', 'poldnev_person')
                                .filter(is_active=True)
                                .filter(expr)
                                .all())
        self._apply_filter(self._last_name_matched, True)
        self._apply_filter(self._good_match, True)
        if not first_name and not birth_date and len(self._candidates) > 1:
            return []
        if strict:
            self._apply_filter(self._sex_matched_or_null)
            self._apply_filter(self._has_poldnev)
            self._apply_filter(self._was_enrolled)
            self._apply_filter(self._has_some_entrance_status)
        return self._candidates

    def _apply_filter(self, func, can_empty=False):
        filtered = list(filter(func, self._candidates))
        if can_empty or filtered:
            self._candidates = filtered

    def _sex_matched_or_null(self, user):
        sex = self._new_user_profile.sex
        if sex and hasattr(user, 'profile') and user.profile.sex:
            return sex == user.profile.sex
        return True

    def _birth_date_matched(self, user):
        birth_date = self._new_user_profile.birth_date
        if birth_date and hasattr(user, 'profile') and user.profile.birth_date:
            return birth_date == user.profile.birth_date
        return False

    def _last_name_matched(self, user):
        last_name = self._new_user_profile.last_name
        ok = False
        if hasattr(user, 'poldnev_person'):
            ok |= match_last_names(last_name, user.poldnev_person.last_name)
        if hasattr(user, 'profile'):
            ok |= match_last_names(last_name, user.profile.last_name)
        ok |= match_last_names(last_name, user.last_name)
        return ok

    def _good_match(self, user):
        first_name = self._new_user_profile.first_name
        birth_date = self._new_user_profile.birth_date
        if (first_name or not birth_date) and self._full_name_matched(user):
            return True
        return self._last_name_matched(user) and self._birth_date_matched(user)

    def _full_name_matched(self, user):
        first_name = self._new_user_profile.first_name
        middle_name = self._new_user_profile.middle_name
        last_name = self._new_user_profile.last_name
        ok = False
        if hasattr(user, 'poldnev_person'):
            ok |= (match_last_names(last_name, user.poldnev_person.last_name)
                   and match_first_names(first_name, user.poldnev_person.first_name)
                   and match_middle_names(middle_name, user.poldnev_person.middle_name))
        if hasattr(user, 'profile'):
            ok |= (match_last_names(last_name, user.profile.last_name)
                   and match_first_names(first_name, user.profile.first_name)
                   and match_middle_names(middle_name, user.profile.middle_name))
        ok |= (match_last_names(last_name, user.last_name)
               and match_first_names(first_name, user.first_name))
        return ok

    @classmethod
    def _has_poldnev(cls, user):
        return hasattr(user, 'poldnev_person')

    @classmethod
    def _was_enrolled(cls, user):
        return entrance_models.EntranceStatus.objects.filter(
            user=user,
            status=entrance_models.EntranceStatus.Status.ENROLLED,
        ).exists()

    @classmethod
    def _has_some_entrance_status(cls, user):
        return entrance_models.EntranceStatus.objects.filter(
            user=user,
        ).exists()
