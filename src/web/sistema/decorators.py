from django.http.response import HttpResponse
from django.shortcuts import render


def form_handler(template_name, form_class, initial_data_constructor=None):
    def decorator(handler):
        def func_wrapper(request, *args, **kwargs):
            if request.method == 'POST':
                form = form_class(data=request.POST)
                if form.is_valid():
                    result = handler(request, form, *args, **kwargs)
                    if result is not None:
                        return result
                return render(request, template_name, {'form': form})
            else:
                initial_data = None
                if initial_data_constructor is not None:
                    initial_data = initial_data_constructor(request)
                if isinstance(initial_data, HttpResponse):
                    return initial_data
                return render(request, template_name, {'form': form_class(initial=initial_data)})

        func_wrapper.__doc__ = handler.__doc__
        func_wrapper.__name__ = handler.__name__
        func_wrapper.__module__ = handler.__module__
        return func_wrapper

    form_handler.__doc__ = decorator.__doc__
    form_handler.__name__ = decorator.__name__
    form_handler.__module__ = decorator.__module__
    return decorator

