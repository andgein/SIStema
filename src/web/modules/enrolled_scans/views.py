import operator

from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect

from modules.enrolled_scans import forms
from sistema.helpers import group_by, respond_as_attachment
import sistema.uploads
from . import models


@login_required
def scans(request):
    submitted_form = None
    if request.method == 'POST':
        submitted_form = forms.EnrolledScanForm(data=request.POST,
                                                files=request.FILES)
        if submitted_form.is_valid():
            save_scan(request.school, request.user, submitted_form)

    all_requirements = (models.EnrolledScanRequirement.objects
                        .filter(school=request.school))
    user_requirements = [r for r in all_requirements
                         if r.is_needed_for_user(request.user)]

    user_scans = group_by(
        models.EnrolledScan.objects.filter(
            requirement__school=request.school,
            user=request.user,
        ).order_by('-created_at'),
        operator.attrgetter('requirement_id')
    )

    for requirement in user_requirements:
        if requirement.id in user_scans:
            requirement.user_scan = user_scans[requirement.id][0]
        else:
            requirement.user_scan = None

        requirement.form = get_form_for_requirement(requirement, submitted_form)

    return render(request, 'enrolled_scans/scans.html', {
        'requirements': user_requirements,
    })


@login_required
def scan(request, requirement_name):
    requirement = get_object_or_404(models.EnrolledScanRequirement,
                                    school=request.school,
                                    short_name=requirement_name)

    user_scan = (models.EnrolledScan.objects
                 .filter(requirement=requirement, user=request.user)
                 .first())

    if user_scan is None:
        return HttpResponseNotFound()

    return respond_as_attachment(
        request, user_scan.filename, user_scan.original_filename)


def save_scan(school, user, submitted_form):
    scan_file = submitted_form.cleaned_data['scan']
    requirement_short_name = (
        submitted_form.cleaned_data['requirement_short_name'])

    saved_file = sistema.uploads.save_file(scan_file, 'enrolled-scans')
    requirement = (
        models.EnrolledScanRequirement.objects
        .filter(school=school, short_name=requirement_short_name)
        .first()
    )

    models.EnrolledScan.objects.create(
        requirement=requirement,
        user=user,
        original_filename=scan_file.name,
        filename=saved_file
    )


def get_form_for_requirement(requirement, submitted_form):
    if submitted_form is not None:
        requirement_short_name = (
            submitted_form.cleaned_data['requirement_short_name'])
        if requirement_short_name == requirement.short_name:
            return submitted_form

    return forms.EnrolledScanForm(requirement.short_name)
