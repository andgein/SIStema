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
    requirements = list(models.EnrolledScanRequirement.objects.filter(school=request.school))
    # Filter only needed for this user requirements
    requirements = list(filter(lambda r: r.is_needed_for_user(request.user), requirements))

    user_scans = group_by(
        models.EnrolledScan.objects.filter(
            requirement__school=request.school,
            user=request.user,
        ).order_by('-created_at'),
        operator.attrgetter('requirement_id')
    )

    for requirement in requirements:
        if requirement.id in user_scans:
            requirement.user_scan = user_scans[requirement.id][0]
        else:
            requirement.user_scan = None
        requirement.form = forms.EnrolledScanForm()

    return render(request, 'enrolled_scans/scans.html', {
        'requirements': requirements,
    })


@login_required
def scan(request, requirement_name):
    requirement = get_object_or_404(models.EnrolledScanRequirement, school=request.school, short_name=requirement_name)

    if request.method == 'POST':
        form = forms.EnrolledScanForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            scan_file = form.cleaned_data['scan']
            saved_file = sistema.uploads.save_file(scan_file, 'enrolled-scans')
            models.EnrolledScan(
                requirement=requirement,
                user=request.user,
                original_filename=scan_file.name,
                filename=saved_file
            ).save()
        else:
            raise Exception(form.errors)
        # TODO: show error message
        return redirect('school:entrance:enrolled_scans:scans', school_name=request.school.short_name)
    else:
        user_scan = models.EnrolledScan.objects.filter(requirement=requirement, user=request.user).first()
        if user_scan is None:
            return HttpResponseNotFound()
        return respond_as_attachment(request, user_scan.filename, user_scan.original_filename)
