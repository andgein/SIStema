import zlib

from django.conf import settings
from django.db import models
from django.utils.encoding import force_bytes, force_str
from django.utils.translation import gettext_lazy as _


class DjangoSettingsReference(object):
    """
    For usage in models.FilePathField or similar field.
    If you use models.FilePathField(path=settings.UPLOAD_DIR) it will be saved
    in migration as models.FilePathField(path='/home/user/projects/.../upload')

    Use DjangoSettingsReference for storing it as a settings's reference, i.e.
    models.FilePathField(path=DjangoSettingsReference('UPLOAD_DIR')). It will be
    saved in migration as
        models.FilePathField(path=DjangoSettingsReference('UPLOAD_DIR'))
    """
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return getattr(settings, self.name)

    def deconstruct(self):
        return "%s.%s" % (__name__, self.__class__.__name__), (self.name,), {}


class CompressedTextField(models.BinaryField):
    description = _("Compressed text field")
    empty_values = [None, '']

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is None:
            return None

        if isinstance(value, str):
            value = zlib.compress(force_bytes(value))

        return super().get_db_prep_value(value, connection, prepared)

    def from_db_value(self, value, expression, connection):
        if isinstance(value, bytes):
            return force_str(zlib.decompress(value))
        return value

    def to_python(self, value):
        if isinstance(value, bytes):
            return force_str(zlib.decompress(value))
        return value
