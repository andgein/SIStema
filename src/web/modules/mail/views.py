from string import whitespace
import os

from django.contrib.auth.decorators import login_required
from django.db.models import Q, TextField
from django.db.models.expressions import Value
from django.db.models.functions import Concat
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags

from . import models, forms
from sistema.helpers import respond_as_attachment
from django.conf import settings
from sistema.uploads import save_file


# Parse recipients from string like: a@mail.ru, b@mail.ru, ...
def _get_recipients(string_with_recipients):
    recipients = []
    for recipient in string_with_recipients.split(', '):
        if recipient == '':
            continue
        query = models.EmailUser.objects.filter(
            Q(sisemailuser__user__email__iexact=recipient) |
            Q(externalemailuser__email__iexact=recipient)
        )
        if query.first() is not None:
            recipients.append(query.first())
        else:
            query = models.PersonalEmail.objects.annotate(
                    full_email=Concat('email_name', Value('-'), 'hash', Value(settings.MAIL_DOMAIN),
                                      output_field=TextField())).filter(full_email__iexact=recipient)
            if query.first() is not None:
                recipients.append(query.first().owner)
            else:
                external_user = models.ExternalEmailUser()
                external_user.email = recipient
                external_user.save()
                recipients.append(external_user)
    return recipients


# Save email to database(if email_id != None edit existing email)
def _save_email(request, email_form, uploaded_files, email_id=None):
    attachments = []
    for file in uploaded_files:
        saved_attachment_filename = os.path.relpath(
            save_file(file, 'mail-attachments'),
            models.Attachment._meta.get_field('file').path
        )
        attachments.append(models.Attachment(
            original_file_name=file.name,
            file_size=file.size,
            content_type=file.content_type,
            file=saved_attachment_filename,
        ))
    email = models.EmailMessage()
    try:
        email.sender = models.SisEmailUser.objects.get(user=request.user)
    except models.EmailUser.DoesNotExist:
        return None
    email.html_text = email_form['email_message']
    email.subject = email_form['email_subject']
    email.id = email_id
    with transaction.atomic():
        email.save()
        for recipient in _get_recipients(email_form['recipients']):
            email.recipients.add(recipient)
        for attachment in attachments:
            attachment.save()
            email.attachments.add(attachment)
        email.save()
    return email


@login_required
def compose(request):
    if request.method == 'POST':
        form = forms.ComposeForm(data=request.POST, files=request.FILES)
    else:
        form = forms.ComposeForm()
    if form.is_valid():
        uploaded_files = request.FILES.getlist('attachments')
        if _save_email(request, form.cleaned_data, uploaded_files) is None:
            return HttpResponseNotFound('Can\'t find your email box.')
        else:
            return redirect('../?result=ok')
    else:
        pass
    return render(request, 'mail/compose.html', {'form': form})


@login_required
def contacts(request):
    NUMBER_OF_RETURNING_RECORDS = 10
    search_request = request.GET['search']
    try:
        email_user = models.SisEmailUser.objects.get(user=request.user)
    except models.EmailUser.DoesNotExist:
        return HttpResponseNotFound("Can't find your mail box.")
    records = models.ContactRecord.objects.filter(
        Q(owner=email_user) & (
            Q(person__sisemailuser__user__email__icontains=search_request) |
            Q(person__sisemailuser__user__first_name__icontains=search_request) |
            Q(person__sisemailuser__user__last_name__icontains=search_request) |
            Q(person__externalemailuser__display_name__icontains=search_request) |
            Q(person__externalemailuser__email__icontains=search_request)
        )
    )[:NUMBER_OF_RETURNING_RECORDS]
    filtered_records = [{'email': rec.person.email, 'display_name': rec.person.display_name}
                        for rec in records]
    return JsonResponse({'records': filtered_records})


def is_sender_of_email(user, email):
    return isinstance(email.sender, models.SisEmailUser) and user == email.sender.user


def is_recipient_of_email(user, email):
    return bool(email.recipients.filter(sisemailuser__user=user) or email.cc_recipients.filter(sisemailuser__user=user))


def can_user_view_message(user, email):
    return is_recipient_of_email(user, email) or is_sender_of_email(user, email)


@login_required
def inbox(request):
    mail_list = models.EmailMessage.objects.filter(
        Q(recipients__sisemailuser__user=request.user) |
        Q(cc_recipients__sisemailuser__user=request.user)
    ).order_by('-created_at')

    return render(request, 'mail/inbox.html', {
        'mail_list': mail_list,
    })


@login_required
def sent(request):
    mail_list = models.EmailMessage.objects.filter(
        sender__sisemailuser__user=request.user,
    ).order_by('-created_at')

    return render(request, 'mail/sent.html', {
        'mail_list': mail_list,
    })


@login_required
def message(request, message_id):
    email = get_object_or_404(models.EmailMessage, id=message_id)

    if not can_user_view_message(request.user, email):
        return HttpResponseForbidden()

    return render(request, 'mail/message.html', {
        'email': email,
        'allow_replying': is_recipient_of_email(request.user, email),
    })

MAX_STRING_LENGTH = 70


def get_citation_depth(string):
    """ Returns the citation depth of a sentence, i.e. 3 for ">>> Hello" and 2 for ">> Hello"  """
    current = 0
    while current < len(string) and string[current] == '>':
        current += 1
    return current


def ensure_beginning_whitespace(string):
    """ Adds a beginning whitespace if necessary """
    if string and string[0] != ' ':
        return ' %s' % string
    return string


def rstrip_if_not_space(line):
    if not line.isspace():
        return line.rstrip()
    return line


def cite_text(text):
    """ Returns cited(quoted) text. Follows RFC 3676. """
    lines = text.split('\n')
    cited_lines = []
    for line in lines:
        depth = get_citation_depth(line)  # Gets the depth of the current citation
        line = line[depth:]  # Deletes the old citation prefix
        new_string_prefix = '>' * (depth + 1)  # Creates the new citation prefix
        current_max_string_length = MAX_STRING_LENGTH - len(new_string_prefix)  # Max length for line without citation
        line = rstrip_if_not_space(line)  # Strips unnecessary whitespaces if line is not a space
        line = line.replace('\r', '')  # Removes all occurrences of '\r'
        while len(line) > current_max_string_length:
            search_position = current_max_string_length
            # Will try to find a whitespace where the line could be split
            while search_position >= 0 and line[search_position] not in whitespace:
                search_position -= 1
            if search_position != -1:  # If an appropriate place to insert a line-break was found
                result = line[:search_position]
                line = line[search_position + 1:]
            else:
                # Will try to find the first whitespace where the line could be split when a word is too long
                search_position = current_max_string_length + 1
                while search_position < len(line) and line[search_position] not in whitespace:
                    search_position += 1
                if search_position != len(line):  # If found
                    result = line[:search_position]
                    line = line[search_position + 1:]
                else:  # If an acceptable position was not found adds the whole line
                    result = line
                    line = ''
            # Add the resulting shortened line
            cited_lines.append('%s%s' % (new_string_prefix, ensure_beginning_whitespace(result)))
        # Add the remainder of the line (if it is not empty)
        if line:
            cited_lines.append('%s%s' % (new_string_prefix, ensure_beginning_whitespace(line)))

    return '\n'.join(cited_lines)


@login_required
def reply(request, message_id):
    email = get_object_or_404(models.EmailMessage, id=message_id)

    if not can_user_view_message(request.user, email):
        return HttpResponseForbidden()

    email_subject = 'Re: %s' % email.subject

    recipients = list()
    recipients.append(email.sender.email)

    for recipient in email.recipients.all():
        if isinstance(recipient, models.ExternalEmailUser) or recipient.user != request.user:
            recipients.append(recipient.email)

    for cc_recipient in email.cc_recipients.all():
        if isinstance(cc_recipient, models.ExternalEmailUser) or cc_recipient.user != request.user:
            recipients.append(cc_recipient.email)

    if email.sender.display_name.isspace():
        display_name = email.sender.email
    else:
        display_name = email.sender.display_name
    text = '\n \n%s:\n%s' % (display_name, cite_text(strip_tags(email.html_text)))

    if request.method == 'POST':
        form = forms.ComposeForm(request.POST)
    else:
        form = forms.ComposeForm(initial={
            'email_subject': email_subject,
            'recipients': ', '.join(recipients),
            'email_message': text,
        })
    if form.is_valid():
        uploaded_files = request.FILES.getlist('attachments')
        if _save_email(request, form.cleaned_data, uploaded_files) is None:
            return HttpResponseNotFound('Can\'t find your email box.')
        else:
            return redirect('../../?result=ok')
    else:
        pass

    return render(request, 'mail/compose.html', {
        'form': form,
    })


@login_required
@require_POST
def delete_email(request, message_id):
    email = get_object_or_404(models.EmailMessage, id=message_id)
    if not can_user_view_message(request.user, email):
        return HttpResponseForbidden()
    email.delete()
    return redirect('/mail')


def can_user_download_attachment(user, attachment):
    return bool(models.EmailMessage.objects.filter(
        Q(attachments=attachment) &
        (Q(sender__sisemailuser__user=user) |
         Q(recipients__sisemailuser__user=user) |
         Q(cc_recipients__sisemailuser__user=user))
    ))


@login_required
def download_attachment(request, attachment_id):
    attachment = get_object_or_404(models.Attachment, id=attachment_id)
    if not can_user_download_attachment(request.user, attachment):
        return HttpResponseForbidden()
    return respond_as_attachment(
        request,
        attachment.get_file_abspath(),
        attachment.original_file_name
    )