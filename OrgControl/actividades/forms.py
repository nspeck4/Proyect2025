from django import forms

from users.models import OrganizationLevel
from .models import PlanAnual, ActividadPlanAnual
from django.contrib.auth import get_user_model

User = get_user_model()


class PlanAnualForm(forms.ModelForm):
    class Meta:
        model = PlanAnual
        fields = ['year', 'organization_level']
        widgets = {
            'year': forms.Select(attrs={'class': 'form-select'}),
            'organization_level': forms.Select(attrs={'class': 'form-select'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.is_superuser:
            self.fields['organization_level'].queryset = OrganizationLevel.objects.filter(
                director=self.user
            )


class ActividadPlanAnualForm(forms.ModelForm):
    class Meta:
        model = ActividadPlanAnual
        fields = ['nombre', 'descripcion', 'responsable', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        plan_id = kwargs.pop('plan_id', None)
        super().__init__(*args, **kwargs)

        if plan_id:
            plan = PlanAnual.objects.get(id=plan_id)
            self.fields['responsable'].queryset = User.objects.filter(
                profile__organizational_level=plan.organization_level
            )