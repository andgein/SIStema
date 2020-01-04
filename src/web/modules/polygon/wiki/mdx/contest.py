import markdown
from django.template.loader import render_to_string

from modules.polygon import models

CONTEST_TAG_RE = r'(?i)\[polygon_contest\s+id:(?P<contest_id>\d+)*\]'


class ContestExtension(markdown.Extension):
    """Contest plugin markdown extension for SIStema wiki."""

    def extendMarkdown(self, md):
        md.inlinePatterns.add(
            'sistema-polygon-contest',
            ContestPattern(CONTEST_TAG_RE, md),
            '>link')


class ContestPattern(markdown.inlinepatterns.Pattern):
    """
    SIStema wiki polygon tag preprocessor. Searches text for
    [polygon_contest id:xxxx] tag and replaces it with the list of problems.
    """

    def handleMatch(self, m):
        contest_id_str = m.group('contest_id')
        contest_id = int(contest_id_str)

        contest = models.Contest.objects.filter(polygon_id=contest_id).first()
        if contest is None:
            return 'Контест с ID {} не существует'.format(contest_id)

        html = render_to_string(
            "polygon/wiki/problem_list.html",
            context={
                'problems': contest.get_problems(),
            })
        return self.markdown.htmlStash.store(html)


def makeExtension(*args, **kwargs):
    """Return an instance of the extension."""
    return ContestExtension(*args, **kwargs)
