from django import shortcuts
from django.contrib import auth

from . import decorators
from questionnaire import views as questionnaire_views


def user(request):
    # TODO(Artem Tabolin): home_page_blocks should probably not be used here,
    #     because it's defined in another module. It's better to make this
    #     dependency at least one-directional.
    blocks = list(request.school.home_page_blocks.order_by('order'))
    for block in blocks:
        block.build(request)
        block.template_name = 'home/%s.html' % block.__class__.__name__

    # TODO(Artem Tabolin): better not to use templates from another module. If
    #     there should be a dependency, then the access to template should be
    #     wrapped in some method.
    return shortcuts.render(request, 'home/user.html', {
        'school': request.school,
        'blocks': blocks,
    })


def staff(request):
    return shortcuts.redirect('school:entrance:enrolling',
                              school_name=request.school.short_name)


@decorators.school_view
def index(request):
    """Returns default page for school for current user."""
    if request.user.is_staff:
        return staff(request)
    else:
        return user(request)


@decorators.school_view
def questionnaire(request, questionnaire_name):
    # TODO(Artem Tabolin): shouldn't redirect be used here instead?
    return questionnaire_views.questionnaire(request, questionnaire_name)
