import sys
import traceback
from allauth.account import adapter


class AccountAdapter(adapter.DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        msg = self.render_mail(template_prefix, email, context)
        try:
            msg.send()
        except Exception:
            sys.stderr.write("Can not send message to email '%s'\n" % email)
            traceback.print_exc(file=sys.stderr)
