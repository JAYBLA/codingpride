from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect
from django.template.loader import get_template
from django.urls import reverse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import CreateView, View
from django.contrib.auth.forms import PasswordChangeForm

from . import forms
from .models import Profile
from .tokens import account_activation_token_generator

User = get_user_model()


class UserRegistrationView(CreateView):
    form_class = forms.UserCreationForm
    template_name = 'registration/signup.html'
    success_url = '/'

    def form_valid(self, form):
        user_email = form.cleaned_data['email']
        user = form.save()
        # send confirmation email
        token = account_activation_token_generator.make_token(user)
        user_id = urlsafe_base64_encode(force_bytes(user.id))
        url = settings.BASE_URL + reverse(
            'accounts:confirm_email',
            kwargs={'user_id': user_id, 'token': token})
        message = get_template(
            'registration/account_activation_email.html'
        ).render({'confirm_url': url})
        mail = EmailMessage(
            'CodingPride Account Confirmation',
            message,
            to=[user_email],
            from_email=settings.EMAIL_HOST_USER)
        mail.content_subtype = 'html'
        mail.send()
        messages.success(self.request,
                         'Please check your email for confimation.')
        return super().form_valid(form)


class ConfirmRegistrationView(View):
    """View for user to confirm registration."""

    def get(self, request, user_id, token):
        user_id = force_text(urlsafe_base64_decode(user_id))

        user = User.objects.get(pk=user_id)

        if user and account_activation_token_generator.check_token(
                user, token):
            user.is_active = True
            Profile.objects.create(user=user)
            user.save()
            messages.success(
                request, ('Registration completed successful. '
                          'Please login to continue..'))

        return redirect('accounts:login')

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/change_password.html', {
        'form': form
    })