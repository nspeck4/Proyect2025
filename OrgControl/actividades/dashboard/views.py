from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Q
from actividades.models import PlanAnual, ActividadPlanAnual


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/executive.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Estadísticas clave
        context['total_planes'] = PlanAnual.objects.count()
        context['planes_aprobados'] = PlanAnual.objects.filter(approved=True).count()

        context['actividades_estado'] = ActividadPlanAnual.objects.values(
            'estado'
        ).annotate(
            total=Count('id')
        ).order_by('estado')

        # Gráfico de avance por nivel organizacional
        context['avance_niveles'] = ActividadPlanAnual.objects.values(
            'plan__organization_level__name'
        ).annotate(
            promedio_avance=models.Avg('avance')
        ).order_by('-promedio_avance')

        return context