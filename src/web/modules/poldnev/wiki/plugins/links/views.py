from django.utils.decorators import method_decorator
from django.views.generic.base import View
from wiki.core.utils import object_to_json_response
from wiki.decorators import get_article

from modules.poldnev import search


class PersonLinkData(View):

    @method_decorator(get_article(can_read=True))
    def dispatch(self, request, article, *args, **kwargs):
        max_num = 20
        query = request.GET.get('query', None)

        matches = []

        if query:
            matches = search.filter_persons(query)
            matches = [
                "[{name}]({url})".format(
                    name=m.first_name + ' ' + m.last_name, url=m.url)
                for m in matches[:max_num]
            ]

        return object_to_json_response(matches)
