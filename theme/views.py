# Create your views here.
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from hs_core.hydroshare import get_resource_types

from mezzanine.accounts.forms import LoginForm
from django.contrib.messages import info
from mezzanine.utils.urls import login_redirect
from mezzanine.utils.views import render
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import (authenticate, login as auth_login)
from django.conf import settings
from django.contrib.auth.decorators import login_required
from mezzanine.accounts import get_profile_form
from django.shortcuts import redirect
from django.core.urlresolvers import NoReverseMatch

def login(request, template="accounts/account_login.html"):
    """
    Login form.
    """
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        authenticated_user = form.save()
        info(request, _("Successfully logged in"))
        pwd = form.cleaned_data['password']
        auth_login(request, authenticated_user)

        if getattr(settings, 'USE_IRODS', False):
            if not getattr(settings, 'IRODS_GLOBAL_SESSION', False): # only create user session when IRODS_GLOBAL_SESSION is set to FALSE
                user = request.user
                if not user.is_superuser: # only create user session when the logged in user is not superuser
                    from hs_core.models import irods_storage
                    if irods_storage.session and irods_storage.environment:
                        try:
                            irods_storage.session.run('iexit full', None, irods_storage.environment.auth)
                        except:
                            pass # try to remove session if there is one, pass without error out if the previous session cannot be removed

                    irods_storage.set_user_session(username=user.get_username(), password=pwd, userid=user.id)

        return login_redirect(request)
    context = {"form": form, "title": _("Log in")}
    return render(request, template, context)

@login_required
def profile_update(request, template="accounts/account_profile_update.html"):
    """
    Profile update form.
    """
    profile_form = get_profile_form()
    form = profile_form(request.POST or None, request.FILES or None,
                        instance=request.user)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        # change corresponding iRODS account password accordingly when USE_IRODS is true but IRODS_GLOBAL_SESSION is FALSE and the user is not superuser
        if getattr(settings, 'USE_IRODS', False) and not getattr(settings, 'IRODS_GLOBAL_SESSION', False) and not request.user.is_superuser:
            # change password for the corresponding iRODS account accordingly upon success
            from django_irods import account
            irods_account = account.IrodsAccount()
            newpwd = form.cleaned_data.get("password1")
            uname = form.cleaned_data.get("username")
            irods_account.setPassward(uname, newpwd)
            # also needs to create a user session corresponding to the user just created to get ready for resource creation
            from hs_core.models import irods_storage
            if irods_storage.session and irods_storage.environment:
                try:
                    irods_storage.session.run('iexit full', None, irods_storage.environment.auth)
                except:
                    pass # try to remove session if there is one, pass without error out if the previous session cannot be removed

            irods_storage.set_user_session(username=uname, password=newpwd, userid=request.user.id)

        info(request, _("Profile updated"))
        try:
            return redirect("profile", username=user.username)
        except NoReverseMatch:
            return redirect("profile_update")
    context = {"form": form, "title": _("Update Profile")}
    return render(request, template, context)

class UserProfileView(TemplateView):
    template_name='accounts/profile.html'

    def get_context_data(self, **kwargs):
        if 'user' in kwargs:
            try:
                u = User.objects.get(pk=int(kwargs['user']))
            except:
                u = User.objects.get(username=kwargs['user'])

        else:
            try:
                u = User.objects.get(pk=int(self.request.GET['user']))
            except:
                u = User.objects.get(username=self.request.GET['user'])

        resource_types = get_resource_types()
        res = []
        for Resource in resource_types:
            res.extend([r for r in Resource.objects.filter(user=u)])

        return {
            'u' : u,
            'resources' :  res
        }
