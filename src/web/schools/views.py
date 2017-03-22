from django import shortcuts
import django.contrib.auth.decorators as auth_decorators

from questionnaire import views as questionnaire_views


@auth_decorators.login_required
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


@auth_decorators.login_required
def staff(request):
    return shortcuts.redirect('school:entrance:enrolling',
                              school_name=request.school.short_name)


@auth_decorators.login_required
def index(request):
    return user(request)


@auth_decorators.login_required
def questionnaire(request, questionnaire_name):
    return questionnaire_views.questionnaire(request, questionnaire_name)
