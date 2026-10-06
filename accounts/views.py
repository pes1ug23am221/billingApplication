from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from .models import InviteToken
from .forms import LoginForm, RegisterForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('billing:dashboard')

    form = LoginForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('billing:dashboard')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


def register_view(request, token):
    invite = get_object_or_404(InviteToken, token=token)

    if not invite.is_valid():
        messages.error(request, 'This invite link has expired or has already been used.')
        return redirect('accounts:login')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.invited_by = invite.created_by
        user.save()

        invite.is_used = True
        invite.used_by = user
        invite.save()

        login(request, user)
        messages.success(request, f'Welcome, {user.first_name or user.username}!')
        return redirect('billing:dashboard')

    return render(request, 'accounts/register.html', {'form': form, 'invite': invite})


@login_required
def invite_view(request):
    if not request.user.is_staff:
        messages.error(request, 'Only admins can create invites.')
        return redirect('billing:dashboard')

    new_invite_url = None

    if request.method == 'POST':
        days = int(request.POST.get('days', 7))
        invite = InviteToken.create_for_user(request.user, days=days)
        new_invite_url = request.build_absolute_uri(f'/accounts/register/{invite.token}/')
        messages.success(request, 'Invite link created!')

    invites = InviteToken.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'accounts/invite.html', {
        'invites': invites,
        'new_invite_url': new_invite_url,
        'now': timezone.now(),
    })
