from django.contrib.auth.tokens import default_token_generator
from djoser import utils
from djoser.conf import settings
from djoser.email import BaseDjoserEmail


class ActivationEmail(BaseDjoserEmail):
    template_name = "activation_email.html"

    def get_context_data(self):
        # ActivationEmail can be deleted
        context = super().get_context_data()

        user = context.get("user")
        context["uid"] = utils.encode_uid(user.pk)
        context["token"] = default_token_generator.make_token(user)
        context["url"] = settings.ACTIVATION_URL.format(**context)
        return context
    
class ConfirmationEmail(BaseDjoserEmail):
    '''Confirmation email for account activation'''
    template_name = "confirmation_email.html"
