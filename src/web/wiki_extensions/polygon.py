from django.conf import settings
import hashlib
import json
import random
import requests
import string
import time


# TODO(artemtab): Parse returned JSON and convert to python objects
class Request:
    """
    Request to Polygon API.

    Usage example:
    >>> request = Request(Request.CONTEST_PROBLEMS,
    ...                   args={'contestId': contest_id})
    >>> response = request.issue()
    >>> problems = response["result"]
    """

    # API methods
    CONTEST_PROBLEMS = 'contest.problems'
    PROBLEMS_LIST = 'problems.list'
    PROBLEM_CHECKER = 'problem.checker'
    PROBLEM_VALIDATOR = 'problem.validator'
    PROBLEM_INTERACTOR = 'problem.interactor'
    PROBLEM_FILES = 'problem.files'
    PROBLEM_SOLUTIONS = 'problem.solutions'
    PROBLEM_VIEW_FILE = 'problem.viewFile'
    PROBLEM_VIEW_SOLUTION = 'problem.viewSolution'
    PROBLEM_SCRIPT = 'problem.script'
    PROBLEM_TESTS = 'problem.tests'
    PROBLEM_TEST_INPUT = 'problem.testInput'
    PROBLEM_TEST_ANSWER = 'problem.testAnswer'
    PROBLEM_SET_VALIDATOR = 'problem.setValidator'
    PROBLEM_SET_CHECKER = 'problem.setChecker'
    PROBLEM_SET_INTERACTOR = 'problem.setInteractor'
    PROBLEM_SAVE_FILE = 'problem.saveFile'
    PROBLEM_SAVE_SOLUTION = 'problem.saveSolution'
    PROBLEM_EDIT_SOLUTION_EXTRA_TAGS = 'problem.editSolutionExtraTags'
    PROBLEM_SAVE_SCRIPT = 'problem.saveScript'
    PROBLEM_SAVE_TEST = 'problem.saveTest'
    PROBLEM_ENABLE_GROUPS = 'problem.enableGroups'
    PROBLEM_ENABLE_POINTS = 'problem.enablePoints'
    PROBLEM_VIEW_TEST_GROUP = 'problem.viewTestGroup'
    PROBLEM_SAVE_TEST_GROUP = 'problem.saveTestGroup'
    PROBLEM_VIEW_TAGS = 'problem.viewTags'
    PROBLEM_SAVE_TAGS = 'problem.saveTags'
    PROBLEM_VIEW_GENERAL_DESCRIPTION = 'problem.viewGeneralDescription'
    PROBLEM_SAVE_GENERAL_DESCRIPTION = 'problem.saveGeneralDescription'
    PROBLEM_VIEW_GENERAL_TUTORIAL = 'problem.viewGeneralTutorial'
    PROBLEM_SAVE_GENERAL_TUTORIAL = 'problem.saveGeneralTutorial'

    def __init__(self, method_name, args=None):
        if args is None:
            args = {}

        self.method_name = method_name
        self.args = args

    def issue(self):
        """Issues request and returns parsed JSON response"""

        api_url = getattr(settings, 'SISTEMA_POLYGON_API_URL', '')
        api_key = getattr(settings, 'SISTEMA_POLYGON_API_KEY', '')
        api_secret = getattr(settings, 'SISTEMA_POLYGON_API_SECRET', '')

        args = dict(self.args)
        args['apiKey'] = api_key
        args['time'] = int(time.time())
        args['apiSig'] = self.get_api_signature(args, api_secret)
        response = requests.get(api_url + self.method_name, params=args)
        return json.loads(response.text)

    def get_api_signature(self, args, api_secret):
        rand_bit = ''.join(
            random.choice(string.ascii_lowercase + string.digits)
            for _ in range(6))

        arg_tuples = list(sorted(args.items()))
        args_bit = '&'.join(key + '=' + str(value) for key, value in arg_tuples)
        api_signature_string = '{}/{}?{}#{}'.format(
            rand_bit, self.method_name, args_bit, api_secret)
        api_signature = (
            rand_bit +
            hashlib.sha512(api_signature_string.encode('utf-8')).hexdigest())
        return api_signature
