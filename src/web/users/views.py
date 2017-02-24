from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import mail, urlresolvers
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django import conf

from sistema import decorators
from users import forms, models


def _force_user_login(request, user):
    # Don't use authenticate(), for details see
    # http://stackoverflow.com/questions/2787650/manually-logging-in-a-user-without-password
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    auth.login(request, user)
    return redirect('home')


def get_email_confirmation_link(request, user):
    return request.build_absolute_uri(urlresolvers.reverse('users:confirm', args=[user.email_confirmation_token]))


def send_confirmation_email(request, user):
    if conf.settings.SISTEMA_SEND_CONFIRMATION_EMAILS:
        # TODO(Artem Tabolin): is it possible to use templates for that?
        link = get_email_confirmation_link(request, user)
        title = 'Регистрация в ЛКШ'
        text = (
            'Здравствуйте, %s %s!\n\nКто-то (возможно, и вы) указали этот адрес '
            'при регистрации в Летней компьютерной школе (https://sistema.lksh.ru). '
            'Для окончания регистрации просто пройдите по этой ссылке: %s\n\nЕсли '
            'вы не регистрировались, игнорируйте это письмо.\n\nС уважением,\n'
            'Команда ЛКШ' % (user.first_name, user.last_name, link))
        res = mail.send_mail(title, text, conf.settings.SERVER_EMAIL, [user.email])
        return res > 0


def get_password_recovery_link(request, recovery):
    return request.build_absolute_uri(urlresolvers.reverse('users:recover', args=[recovery.recovery_token]))


def send_password_recovery_email(request, recovery):
    user = recovery.user
    link = get_password_recovery_link(request, recovery)
    title = 'Восстановление пароля в ЛКШ'
    text = (
        'Здравствуйте, %s %s!\n\nДля восстановления пароля просто пройдите по '
        'этой ссылке: %s\n\nС уважением,\nКоманда ЛКШ' %
        (user.first_name, user.last_name, link))
    res = mail.send_mail(title, text, conf.settings.SERVER_EMAIL, [user.email])
    return res > 0


def fill_auth_form(request):
    if request.user.is_authenticated:
        return redirect('home')
    return None

@transaction.atomic
@decorators.form_handler('user/login.html', forms.AuthForm, fill_auth_form)
def login(request, form):
    user = auth.authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password'])
    if user is not None:
        if not user.is_email_confirmed:
            form.add_error('email', 'Электронная почта не подтверждена. Перейдите по ссылке из письма')
            return None

        auth.login(request, user)
        return redirect('home')

    form.add_error('password', 'Неверный пароль')
    return None


@transaction.atomic
@decorators.form_handler('user/registration.html', forms.RegistrationForm)
def register(request, form):
    email = form.cleaned_data['email']

    if models.User.objects.filter(username=email).exists():
        # TODO: make link to forgot-password
        form.add_error('email', 'Вы уже зарегистрированы. Забыли пароль?')
        return None

    password = form.cleaned_data['password']
    first_name = form.cleaned_data['first_name']
    last_name = form.cleaned_data['last_name']
    user = models.User.objects.create_user(username=email,
                                           email=email,
                                           password=password,
                                           first_name=first_name,
                                           last_name=last_name,
                                           )
    user.is_email_confirmed = False
    user.save()

    send_confirmation_email(request, user)

    return _force_user_login(request, user)


def fill_complete_form(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('users:login')
    if user.is_email_confirmed or not conf.settings.SISTEMA_SEND_CONFIRMATION_EMAILS:
        return redirect('home')
    return {'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            }


@transaction.atomic
@decorators.form_handler('user/complete.html',
                         forms.CompleteUserCreationForm,
                         fill_complete_form)
def complete(request, form):
    email = form.cleaned_data['email']

    if models.User.objects.filter(username=email).exists():
        # TODO: make link to forgot-password
        form.add_error('email', 'Вы уже зарегистрированы. Забыли пароль?')
        return None

    request.user.email = email
    request.user.username = request.user.email
    request.user.first_name = form.cleaned_data['first_name']
    request.user.last_name = form.cleaned_data['last_name']
    request.user.set_password(form.cleaned_data['password'])
    request.user.is_email_confirmed = False
    request.user.save()

    send_confirmation_email(request, request.user)

    return redirect('home')


# TODO: only POST with csrf token
@login_required
def logout(request):
    auth.logout(request)
    return redirect('home')


@transaction.atomic
def confirm(request, token):
    user = get_object_or_404(models.User, email_confirmation_token=token)

    user.is_email_confirmed = True
    user.save()

    return _force_user_login(request, user)


@decorators.form_handler('user/forgot.html',
                         forms.ForgotPasswordForm)
def forgot(request, form):
    email = form.cleaned_data['email']

    if not models.User.objects.filter(username=email).exists():
        form.add_error('email', 'Пользователя с таким адресом не зарегистрировано')
        return None

    user = models.User.objects.filter(username=email).get()
    recovery = models.UserPasswordRecovery(user=user)
    recovery.save()

    # TODO: show form with message "We've send an email to you"
    send_password_recovery_email(request, recovery)
    return redirect('home')


@decorators.form_handler('user/recover.html',
                         forms.PasswordRecoveryForm)
def recover(request, form, token):
    recoveries = models.UserPasswordRecovery.objects.filter(recovery_token=token, is_used=False)
    if recoveries.exists():
        recovery = recoveries.first()
        recovery.is_used = True
        recovery.save()

        user = recovery.user
        user.set_password(form.cleaned_data['password'])
        user.save()

        return _force_user_login(request, user)

    return None
