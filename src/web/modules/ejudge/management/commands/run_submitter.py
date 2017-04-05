import time
import traceback
import urllib.parse
from bs4 import BeautifulSoup
import requests

from django.core.management.base import BaseCommand
from django.db import transaction

from ... import models
from sistema import settings


class EjudgeException(Exception):
    pass


class CantSubmitEjudgeException(EjudgeException):
    pass


class Command(BaseCommand):
    help = 'Run ejudge submitter for submitted solutions by users'
    TIME_INTERVAL = 0.5  # in seconds

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backend_address = settings.SISTEMA_EJUDGE_BACKEND_ADDRESS
        self.ejudge_login = settings.SISTEMA_EJUDGE_USER
        self.ejudge_password = settings.SISTEMA_EJUDGE_PASSWORD
        self.session = requests.session()

    @staticmethod
    def _find_between(text, pre, post):
        start_pos = text.find(pre)
        finish_pos = text.find(post, start_pos)
        if finish_pos < 0:
            finish_pos = len(text)
        return text[start_pos+len(pre):finish_pos]

    # TODO: extract to EjudgeApi
    def _login(self, contest_id):
        self.stdout.write('Try to authorize in ejudge with login %s and password %s' % (
            self.ejudge_login, '*' * len(self.ejudge_password)))
        # TODO: build address with library functions
        login_url = '%s/cgi-bin/new-client' % (self.backend_address,)
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
        submit_url = '%s/cgi-bin/new-client' % (self.backend_address,)
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

    def _get_ejudge_run_status_from_url(self, runs_url, ejudge_sid, submit_id):
        r = self.session.get(runs_url)
        if r.status_code != 200:
            raise EjudgeException('Bad http status code: %d' % r.status_code)

        parsed = BeautifulSoup(r.text)
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

        return None, None, None

    def _get_ejudge_run_status(self, contest_id, submit_id):
        ejudge_sid = self._login(contest_id)
        runs_url = '%s/cgi-bin/new-client?SID=%s&action=140' % (self.backend_address, ejudge_sid)
        result, failed_test, score = self._get_ejudge_run_status_from_url(runs_url, ejudge_sid, submit_id)
        if result is None:
            runs_url = '%s/cgi-bin/new-client?SID=%s&action=140&all_runs=1' % (self.backend_address, ejudge_sid)
            result, failed_test, score = self._get_ejudge_run_status_from_url(runs_url, ejudge_sid, submit_id)

        return result, failed_test, score

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
        not_fetched = models.QueueElement.objects.filter(status=models.QueueElement.Status.NOT_FETCHED) \
            .select_related('language')
        for queue_element in not_fetched:
            try:
                # TODO: For Django 1.9 use self.style.SUCCESS
                self.stdout.write('Found new submit #%d in queue to contest %d, problem %d, created at %s, file %s' % (
                    queue_element.id,
                    queue_element.ejudge_contest_id,
                    queue_element.ejudge_problem_id,
                    queue_element.created_at,
                    queue_element.file_name))

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
                    self.stdout.write('Set status for queue element %d to SUBMITTED' % (queue_element.id, ))
                    submission = models.Submission(ejudge_contest_id=queue_element.ejudge_contest_id,
                                                   ejudge_submit_id=ejudge_submit_id)
                    submission.save()

                    queue_element.status = models.QueueElement.Status.SUBMITTED
                    queue_element.submission = submission
                    queue_element.save()
            except Exception as e:
                self.stdout.write(self.style.ERROR('Exception while submit solution to ejudge: %s' % e))
                traceback.print_exc()

    def _process_submitted(self):
        submitted = models.QueueElement.objects.filter(status=models.QueueElement.Status.SUBMITTED)
        for queue_element in submitted:
            try:
                self.stdout.write('Checking solution status in ejudge: contest %d, run %d' % (
                    queue_element.submission.ejudge_contest_id,
                    queue_element.submission.ejudge_submit_id))

                result, failed_test, score = self._get_ejudge_run_status(queue_element.submission.ejudge_contest_id,
                                                                  queue_element.submission.ejudge_submit_id)
                if result is None:
                    self.stdout.write('Hmmm, strange.. I can\'t found run in ejudge: queue element #%d' % queue_element.id)
                    continue

                if result in ['Running...', 'Waiting...', 'Compiling...', 'Compiled']:
                    self.stdout.write('Submission has not been checked yet: result is %s' % result)
                    continue
                self.stdout.write('Submission has been checked: result is %s' % result)
                with transaction.atomic():
                    checking_result = models.SolutionCheckingResult(
                        result=models.CheckingResult.Result.from_ejudge_status(result),
                        failed_test=failed_test,
                        score=score,
                    )
                    checking_result.save()
                    queue_element.submission.result = checking_result
                    queue_element.submission.save()

                    queue_element.status = models.QueueElement.Status.CHECKED
                    queue_element.save()

            except Exception as e:
                self.stdout.write(self.style.ERROR('Exception while checking solution from ejudge: %s' % e))
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
