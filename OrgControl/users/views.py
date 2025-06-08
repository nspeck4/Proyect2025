from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import CustomUser, OrganizationLevel, ApprovalFlow, ApproverRole, UserProfile
from .forms import CustomUserCreationForm, OrganizationLevelForm, ApproverRoleForm, CustomUserChangeForm
from .forms import UserProfileForm



@login_required
def create_user(request):
    if not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:user_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/user_form.html', {'form': form})


class UserListView(LoginRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_url = reverse_lazy('users:user_list')

    def test_func(self):
        return self.request.user.is_superuser


class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user_list')

    def test_func(self):
        return self.request.user.is_superuser


@login_required
def organization_structure(request):
    levels = OrganizationLevel.objects.all()
    return render(request, 'users/organization_structure.html', {'levels': levels})


@login_required
def create_organization_level(request):
    if not request.user.is_superuser:
        return redirect('home')

    if request.method == 'POST':
        form = OrganizationLevelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users:organization_structure')
    else:
        form = OrganizationLevelForm()

    return render(request, 'users/organization_level_form.html', {'form': form})


@login_required
def approval_flows(request):
    flows = ApprovalFlow.objects.all()
    return render(request, 'users/approval_flows.html', {'flows': flows})


@login_required
def manage_approvers(request, flow_id):
    flow = get_object_or_404(ApprovalFlow, pk=flow_id)
    approvers = ApproverRole.objects.filter(flow=flow).order_by('approval_order')

    if request.method == 'POST':
        form = ApproverRoleForm(request.POST)
        if form.is_valid():
            approver = form.save(commit=False)
            approver.flow = flow
            approver.save()
            return redirect('users:manage_approvers', flow_id=flow.id)
    else:
        form = ApproverRoleForm(initial={'flow': flow})

    return render(request, 'users/manage_approvers.html', {
        'flow': flow,
        'approvers': approvers,
        'form': form
    })
@login_required
def profile_view(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, 'users/profile.html', {'profile': profile})

@login_required
def profile_edit(request):
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_view')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'users/profile_edit.html', {'form': form})

@login_required
def staff_directory(request):
    profiles = UserProfile.objects.select_related('user', 'department').all()
    return render(request, 'users/directory.html', {'profiles': profiles})