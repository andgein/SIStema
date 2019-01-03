import re

from django.conf import settings
from django.core import management
from django.utils import translation
from wiki import models
from wiki_extensions import polygon
import django.core.mail


class Command(management.base.BaseCommand):
    help = 'Update contests in wiki articles from Polygon'

    requires_migrations_checks = True

    open_tag_regex = re.compile(r'<!--\s+contest:\s+polygon:(?P<id>\d+)\s+-->')
    close_tag_regex = re.compile(r'<!--\s+endcontest\s+-->')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error = None

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)

        articles = (
            models.Article.objects
            .select_related())
        for article in articles:
            old_content = article.current_revision.content

            new_content = self.replace_contest_data(old_content)
            if new_content is None:
                # Error
                message = '{}: {}'.format(article.current_revision.title,
                                          self.error)
                print(message)
                django.core.mail.mail_admins('Wiki update from Polygon failed',
                                             message)
                continue

            if new_content == old_content:
                # Nothing changed, do nothing
                continue

            print('Updating article:', article.current_revision.title)

            # Text was changed. Creating new revision
            new_revision = models.ArticleRevision()
            new_revision.inherit_predecessor(article)
            new_revision.content = new_content
            new_revision.user_message = (
                'Автоматическое обновление контестов из Полигона')
            article.add_revision(new_revision)

    def replace_contest_data(self, old_content):
        tokens = self.tokenize(old_content)
        new_content_bits = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            i += 1

            if token.type == Token.STRING:
                new_content_bits.append(token.string)
                continue

            if token.type == Token.CLOSE_TAG:
                self.error = 'Unexpected close tag'
                return

            if token.type == Token.OPEN_TAG:
                contest_id = token.contest_id
                new_content_bits.append(token.string)

                if i >= len(tokens):
                    self.error = 'Unexpected end of article'
                    return
                token = tokens[i]
                i += 1
                if token.type == Token.STRING:
                    if i >= len(tokens):
                        self.error = 'Unexpected end of article'
                        return
                    token = tokens[i]
                    i += 1

                if token.type != Token.CLOSE_TAG:
                    self.error = 'Expected close tag, but found ' + token.type
                    return

                new_content_bits.append(
                    self.fetch_contest_description(contest_id))
                new_content_bits.append(token.string)

        return ''.join(new_content_bits)

    def tokenize(self, text):
        open_matches = [
            (match.start(), match.end(), Token(Token.OPEN_TAG,
                                               contest_id=match.group('id'),
                                               string=match.group(0)))
            for match in re.finditer(self.open_tag_regex, text)
        ]
        close_matches = [
            (match.start(), match.end(), Token(Token.CLOSE_TAG,
                                               string=match.group(0)))
            for match in re.finditer(self.close_tag_regex, text)
        ]
        matches = open_matches + close_matches
        matches.sort(key=lambda x: (x[0], x[1]))
        tokens = []
        next_index = 0
        for start, end, token in matches:
            if next_index < start:
                tokens.append(Token(Token.STRING,
                                    string=text[next_index:start]))
            tokens.append(token)
            next_index = end
        if next_index < len(text):
            tokens.append(Token(Token.STRING, string=text[next_index:]))
        return tokens

    def fetch_contest_description(self, contest_id):
        request = polygon.Request(polygon.Request.CONTEST_PROBLEMS,
                                  args={'contestId': contest_id})
        problems = request.issue()['result']
        # Keys are A, B, etc. Sort them to get problems in the right order
        keys = list(sorted(problems.keys()))

        description_bits = ['\n']
        for key in keys:
            problem = problems[key]
            request = polygon.Request(
                polygon.Request.PROBLEM_VIEW_GENERAL_DESCRIPTION,
                args={'problemId': problem['id']})
            description = request.issue()['result']
            description_bits.append(
                "1. `{name}:{id}` — {description}\n"
                .format(name=problem["name"],
                        id=problem["id"],
                        description=description))

        return ''.join(description_bits)


class Token:
    STRING = 'string'
    OPEN_TAG = 'open-tag'
    CLOSE_TAG = 'close-tag'

    def __init__(self, token_type, contest_id=None, string=None):
        self.type = token_type
        self.contest_id = contest_id
        self.string = string
