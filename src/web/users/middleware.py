from django import shortcuts, http


class UserProfileMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.user_profile = None
        if request.user.is_authenticated:
            if request.user.is_staff:
                return None
            if hasattr(request.user, 'user_profile'):
                request.user_profile = request.user.user_profile
            else:
                if hasattr(request, 'school'):
                    redirect_url = shortcuts.resolve_url('user:profile')
                    return http.HttpResponseRedirect(redirect_url)
        return None
