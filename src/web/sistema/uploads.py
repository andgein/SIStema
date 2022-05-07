import os.path
import string
import random
from typing import Optional

from . import settings


def _ensure_directory_exists(path: str):
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        if not os.path.isdir(path):
            raise FileNotFoundError('sistema: %s is not a directory' % path)


def _generate_random_name(length: int = 10, alphabet: str = string.hexdigits):
    return ''.join(random.choice(alphabet) for _ in range(length))


# TODO: by default save extension from uploaded_file
def save_file(uploaded_file, category: str, extension: Optional[str] = None) -> str:
    DEFAULT_EXTENSION = ''

    directory = os.path.join(settings.SISTEMA_UPLOAD_FILES_DIR, category)
    _ensure_directory_exists(directory)

    file_name = os.path.join(directory, _generate_random_name())
    if extension is None:
        extension = DEFAULT_EXTENSION
    if extension != '':
        file_name += '.' + extension

    with open(file_name, 'wb') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    return file_name
