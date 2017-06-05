from django import forms

import frontend.forms


class EnrolledScanForm(forms.Form):
    scan = frontend.forms.RestrictedFileField(max_upload_size=2 * 1024 * 1024,
                                              required=True,
                                              label='',
                                              label_suffix='')

    requirement_short_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, requirement_short_name=None, *args, **kwargs):
        if requirement_short_name is not None:
            initial = kwargs.get('initial', {})
            initial['requirement_short_name'] = requirement_short_name
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
