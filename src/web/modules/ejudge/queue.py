from . import models


def add_from_file(ejudge_contest_id, ejudge_problem_id,
                  language: models.ProgrammingLanguage, file_name):
    element = models.QueueElement(
        ejudge_contest_id=ejudge_contest_id,
        ejudge_problem_id=ejudge_problem_id,
        language=language,
        file_name=file_name
    )
    element.save()
    return element
