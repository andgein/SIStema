import time
import traceback
import urllib.parse
from bs4 import BeautifulSoup
import requests

from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings

from constance import config

from modules.ejudge import models


EJUDGE_SUBMISSIONS_LIMIT = 13


class EjudgeException(Exception):
    pass


class CantSubmitEjudgeException(EjudgeException):
    pass


class Command(BaseCommand):
    help = 'Run ejudge submitter for submitted solutions by users'
    TIME_INTERVAL = 0.5  # in seconds

    runs_page_cache = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_address = config.SISTEMA_EJUDGE_BACKEND_ADDRESS
        self.ejudge_login = config.SISTEMA_EJUDGE_USER
        self.ejudge_password = config.SISTEMA_EJUDGE_PASSWORD
        self.session = requests.session()

    @staticmethod
    def _find_between(text, pre, post):
        start_pos = text.find(pre)
        finish_pos = text.find(post, start_pos)
        if finish_pos < 0:
            finish_pos = len(text)
        return text[start_pos+len(pre):finish_pos]

    def _build_client_url(self, sid='', action=0, additional_params=''):
        params = ''
        if sid != '':
            params += '&SID=%s' % (sid, )
        if action > 0:
            params += '&action=%d' % (action, )
        if additional_params != '':
            params += '&%s' % (additional_params, )
        if params.startswith('&'):
            params = '?' + params[1:]

        # TODO (andgein): build address with library functions
        return '%s/cgi-bin/new-client%s' % (self.backend_address, params)

    # TODO (andgein): extract to EjudgeApi
    def _login(self, contest_id):
        self.stdout.write(
            'Try to authorize in ejudge with login %s and password %s' % (
                self.ejudge_login, '*' * len(self.ejudge_password)
            )
        )
        login_url = self._build_client_url()
        login_data = {'contest_id': contest_id,
                      'role': 0,
                      'prob_name': '',
                      'login': self.ejudge_login,
                      'password': self.ejudge_password,
                      'locale_id': 0}
        r = self.session.post(login_url, login_data)
        if r.status_code != 200:
            raise EjudgeException('Invalid http status code: %d' % r.status_code)

        self.stdout.write('Success: current url is %s' % r.url)
        new_url = urllib.parse.urlparse(r.url)
        qs = urllib.parse.parse_qs(new_url.query)
        if 'SID' not in qs:
            raise EjudgeException('Can\'t find param SID in url: %s' % r.url)
        sid = qs['SID'][0]
        self.stdout.write('Current SID is %s' % sid)
        return sid

    def _submit_to_ejudge(self, sid, problem_id, language_id, file_name):
        submit_url = self._build_client_url()
        submit_data = {'SID': sid,
                       'prob_id': problem_id,
                       'lang_id': language_id,
                       'action_40': True,
                       }
        with open(file_name, 'rb') as opened_file:
            files = {'file': opened_file}
            r = self.session.post(submit_url, submit_data, files=files)

        if r.status_code != 200:
            raise EjudgeException('Bad http status code: %d' % r.status_code)

        error_string = 'Error: '
        if error_string in r.text:
            error_message = self._find_between(r.text, error_string, '<')
            raise CantSubmitEjudgeException(error_message)

        # TODO: use bs4?
        run_id_pre = '<td class="b1">'
        run_id_post = '</td>'
        run_id = self._find_between(r.text, run_id_pre, run_id_post)
        try:
            run_id = int(run_id)
        except:
            raise EjudgeException('Invalid non-numeric run_id: %s' % run_id)

        return run_id

    def _get_ejudge_run_status_from_url(self, runs_url, submit_id, force_load=False):
        if not self.runs_page_cache or force_load:
            r = self.session.get(runs_url)
            if r.status_code != 200:
                raise EjudgeException('Bad http status code: %d' % r.status_code)
            page_content = r.text
            self.runs_page_cache = page_content
        else:
            page_content = self.runs_page_cache

        parsed = BeautifulSoup(page_content)
        table = parsed.find(attrs={'class': 'table'})
        for tr in table.find_all('tr')[1:]:
            tds = tr.find_all('td')
            # Run_id, Time, Size, Problem, Language, Result, Failed Test, Report
            run_id = tds[0].get_text()
            if run_id == str(submit_id):
                result = tds[5].get_text()
                failed_test = tds[6].get_text()
                try:
                    failed_test = int(failed_test)
                except Exception:
                    failed_test = None

                score = None
                if result == 'Partial solution':
                    try:
                        score = int(tds[7].get_text())
                    except Exception:
                        pass

                return result, failed_test, score

        if not force_load:
            return self._get_ejudge_run_status_from_url(
                runs_url, submit_id, force_load=True
            )
        return None, None, None

    def _get_ejudge_run_status(self, contest_id, submit_id):
        ejudge_sid = self._login(contest_id)
        runs_url = self._build_client_url(ejudge_sid, 140)
        result, failed_test, score = self._get_ejudge_run_status_from_url(
            runs_url,
            submit_id
        )
        if result is not None:
            return result, failed_test, score

        runs_url = self._build_client_url(ejudge_sid, 140, 'all_runs=1')
        return self._get_ejudge_run_status_from_url(
            runs_url,
            submit_id
        )

    def _get_ejudge_run_report(self, contest_id, submit_id):
        ejudge_sid = self._login(contest_id)
        report_url = self._build_client_url(
            ejudge_sid, 37, 'run_id=%d' % (submit_id, )
        )
        self.stdout.write('Try to get report for submission from url: %s' % (
            report_url,
        ))

        r = self.session.get(report_url)
        if r.status_code != 200:
            raise EjudgeException('Bad http status code: %d' % r.status_code)

        soup = BeautifulSoup(r.text)
        pres = soup.find_all('pre')
        if len(pres) < 1:
            return ''

        return pres[0].get_text()

    def _submit_solution(self, contest_id, problem_id, language, file_name):
        ejudge_sid = self._login(contest_id)
        language_ejudge_id = None if language is None else language.ejudge_id
        ejudge_submit_id = self._submit_to_ejudge(
            ejudge_sid,
            problem_id,
            language_ejudge_id,
            file_name
        )

        return ejudge_submit_id

    def _process_not_submitted(self):
        submitted_count = len(models.QueueElement.objects.filter(
            status=models.QueueElement.Status.SUBMITTED
        ))
        limit = max(0, EJUDGE_SUBMISSIONS_LIMIT - submitted_count)
        not_fetched = (
            models.QueueElement.objects
            .filter(status=models.QueueElement.Status.NOT_FETCHED)
            .select_related('language')
        )[:limit]
        for queue_element in not_fetched:
            try:
                self.stdout.write(self.style.SUCCESS(
                    'Found new submission #%d in queue: '
                    'to contest %d, problem %d, created at %s, file %s' % (
                        queue_element.id,
                        queue_element.ejudge_contest_id,
                        queue_element.ejudge_problem_id,
                        queue_element.created_at,
                        queue_element.file_name)
                ))

                try:
                    ejudge_submit_id = self._submit_solution(
                        queue_element.ejudge_contest_id,
                        queue_element.ejudge_problem_id,
                        queue_element.language,
                        queue_element.file_name
                    )
                except CantSubmitEjudgeException as e:
                    self.stdout.write('Can\'t submit: %s' % (e, ))
                    queue_element.status = models.QueueElement.Status.WONT_CHECK
                    queue_element.wont_check_message = str(e)
                    queue_element.save()
                    continue

                with transaction.atomic():
                    self.stdout.write(
                        'Set status for queue element %d to SUBMITTED' % (
                            queue_element.id,
                        )
                    )
                    submission = models.Submission(
                        ejudge_contest_id=queue_element.ejudge_contest_id,
                        ejudge_submit_id=ejudge_submit_id
                    )
                    submission.save()

                    queue_element.status = models.QueueElement.Status.SUBMITTED
                    queue_element.submission = submission
                    queue_element.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    'Exception while submitting solution to ejudge: %s' % e
                ))
                traceback.print_exc()

    def _process_submitted(self):
        submitted = models.QueueElement.objects.filter(
            status=models.QueueElement.Status.SUBMITTED
        )
        for queue_element in submitted:
            contest_id = queue_element.submission.ejudge_contest_id
            submit_id = queue_element.submission.ejudge_submit_id

            try:
                self.stdout.write(
                    'Checking submission status in ejudge: '
                    'contest %d, run %d' % (contest_id, submit_id)
                )

                ejudge_result, failed_test, score = self._get_ejudge_run_status(
                    contest_id, submit_id
                )
                if ejudge_result is None:
                    self.stdout.write(
                        'Hmmm, it\'s very strange... '
                        'I can\'t found run in ejudge: queue element #%d' %
                        (queue_element.id, )
                    )
                    continue

                if ejudge_result in ['Running...', 'Waiting...',
                                     'Compiling...', 'Compiled']:
                    self.stdout.write(
                        'Submission has not been checked yet: '
                        'status is %s' % (ejudge_result, ))
                    continue

                report = self._get_ejudge_run_report(contest_id, submit_id)

                self.stdout.write(
                    'Submission has been checked: '
                    'result is %s' % ejudge_result
                )
                result = models.CheckingResult.Result.from_ejudge_status(
                    ejudge_result
                )
                with transaction.atomic():
                    checking_result = models.SolutionCheckingResult(
                        result=result,
                        failed_test=failed_test,
                        score=score,
                        report=report,
                    )
                    checking_result.save()
                    queue_element.submission.result = checking_result
                    queue_element.submission.save()

                    queue_element.status = models.QueueElement.Status.CHECKED
                    queue_element.save()

            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    'Exception while checking submission status in ejudge: %s' %
                    (e, )
                ))
                traceback.print_exc()

    def _one_step(self):
        try:
            self._process_not_submitted()
            self._process_submitted()
        except Exception as e:
            self.stdout.write('Some strange exception: %s' % e)
            traceback.print_exc()

    def handle(self, *args, **options):
        self.stdout.write('Starting ejudge submitter')
        while True:
            self._one_step()
            time.sleep(self.TIME_INTERVAL)
