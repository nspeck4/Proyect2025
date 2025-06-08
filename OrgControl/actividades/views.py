from http.client import HTTPResponse

from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import PlanAnual, ActividadPlanAnual
from .forms import PlanAnualForm, ActividadPlanAnualForm
from openpyxl import Workbook
from django.views import View

class PlanAnualListView(LoginRequiredMixin, ListView):
    model = PlanAnual
    template_name = 'actividades/plan_anual_list.html'
    context_object_name = 'planes'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                organization_level__director=self.request.user
            )
        return queryset.select_related('organization_level', 'created_by')

class PlanAnualCreateView(LoginRequiredMixin, CreateView):
    model = PlanAnual
    form_class = PlanAnualForm
    template_name = 'actividades/plan_anual_form.html'
    success_url = reverse_lazy('plan_anual_list')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class PlanAnualDetailView(LoginRequiredMixin, DetailView):
    model = PlanAnual
    template_name = 'actividades/plan_anual_detail.html'
    context_object_name = 'plan'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actividades'] = self.object.actividades.all()
        return context

class ActividadCreateView(LoginRequiredMixin, CreateView):
    model = ActividadPlanAnual
    form_class = ActividadPlanAnualForm
    template_name = 'actividades/actividad_form.html'

    def get_success_url(self):
        return reverse_lazy('plan_anual_detail', kwargs={'pk': self.kwargs['plan_id']})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['plan_id'] = self.kwargs['plan_id']
        return kwargs

    def form_valid(self, form):
        plan = PlanAnual.object.get(id=self.kwargs['plan_id'])
        form.instance.plan = plan
        return super().form_valid(form)


class AprobacionesPendientesListView(LoginRequiredMixin, ListView):
    model = Aprobacion
    template_name = 'actividades/aprobaciones_pendientes.html'
    context_object_name = 'aprobaciones'

    def get_queryset(self):
        return self.request.user.aprobaciones_pendientes.filter(estado='P')


class AprobarActividadView(LoginRequiredMixin, UpdateView):
    model = Aprobacion
    fields = ['estado', 'comentarios']
    template_name = 'actividades/aprobar_actividad.html'

    def get_success_url(self):
        return reverse_lazy('aprobaciones_pendientes')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.actividad.verificar_estado_aprobacion()
        return response


class GenerarReportePDF(View):
    def get(self, request, plan_id):
        response = HTTPResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="plan_{plan_id}.pdf"'

        p = canvas.Canvas(response)
        plan = PlanAnual.objects.get(id=plan_id)

        # Cabecera
        p.drawString(100, 800, f"Plan Anual {plan.year}")
        p.drawString(100, 780, f"Nivel: {plan.organization_level}")

        # Contenido
        y = 750
        for actividad in plan.actividades.all():
            p.drawString(100, y, f"- {actividad.nombre} ({actividad.get_estado_display()})")
            y -= 20

        p.showPage()
        p.save()
        return response


class GenerarReporteExcel(View):
    def get(self, request, plan_id):
        response = HTTPResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="plan_{plan_id}.xlsx"'

        wb = Workbook()
        ws = wb.active
        ws.title = f"Plan {plan_id}"

        plan = PlanAnual.objects.get(id=plan_id)

        # Cabecera
        ws.append(['Plan Anual', plan.year, plan.organization_level.name])
        ws.append([])
        ws.append(['Actividad', 'Responsable', 'Estado', 'Avance'])
        # Datos
        for actividad in plan.actividades.all():
            ws.append([
                actividad.nombre,
                actividad.responsable.get_full_name(),
                actividad.get_estado_display(),
                f"{actividad.avance}%"
            ])

        wb.save(response)
        return response