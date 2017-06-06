from django import forms

import frontend.forms


class EnrolledScanForm(forms.Form):
    scan = frontend.forms.RestrictedFileField(max_upload_size=2 * 1024 * 1024,
                                              required=True,
                                              label='',
                                              label_suffix='')

    requirement_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, requirement_id=None, *args, **kwargs):
        if requirement_id is not None:
            initial = kwargs.get('initial', {})
            initial['requirement_id'] = requirement_id
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
