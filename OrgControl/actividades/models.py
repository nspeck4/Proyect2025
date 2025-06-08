from datetime import timezone
from django.core.validators import MaxLengthValidator
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from users.models import OrganizationLevel
from django.core.mail import send_mail
from django.template.loader import render_to_string


class PlanAnual(models.Model):
    """Modelo para los planes anuales de la organización"""
    YEAR_CHOICES = [(y, str(y)) for y in range(2023, 2031)]

    year = models.IntegerField(
        _('Año'),
        choices=YEAR_CHOICES,
        unique=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='planes_creados',
        verbose_name=_('Creado por')
    )
    created_at = models.DateTimeField(
        _('Fecha de creación'),
        auto_now_add=True
    )
    approved = models.BooleanField(
        _('Aprobado'),
        default=False
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='planes_aprobados',
        verbose_name=_('Aprobado por')
    )
    organization_level = models.ForeignKey(
        OrganizationLevel,
        on_delete=models.PROTECT,
        verbose_name=_('Nivel organizacional')
    )

    class Meta:
        verbose_name = _('Plan Anual')
        verbose_name_plural = _('Planes Anuales')
        ordering = ['-year']
        constraints = [
            models.UniqueConstraint(
                fields=['year', 'organization_level'],
                name='unique_plan_anual'
            )
        ]

    def __str__(self):
        return f"Plan Anual {self.year} - {self.organization_level}"


class ActividadPlanAnual(models.Model):
    """Actividades específicas dentro de un plan anual"""
    ESTADO_CHOICES = [
        ('P', _('Pendiente')),
        ('E', _('En progreso')),
        ('C', _('Completado')),
        ('A', _('Aprobado')),
        ('R', _('Rechazado'))
    ]

    plan = models.ForeignKey(
        PlanAnual,
        on_delete=models.CASCADE,
        related_name='actividades',
        verbose_name=_('Plan Anual')
    )
    nombre = models.CharField(
        _('Nombre de la actividad'),
        max_length=200
    )
    descripcion = models.TextField(
        _('Descripción detallada'),
        blank=True
    )
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='actividades_asignadas',
        verbose_name=_('Responsable')
    )
    fecha_inicio = models.DateField(
        _('Fecha de inicio')
    )
    fecha_fin = models.DateField(
        _('Fecha de finalización')
    )
    estado = models.CharField(
        _('Estado'),
        max_length=1,
        choices=ESTADO_CHOICES,
        default='P'
    )
    avance = models.PositiveIntegerField(
        _('Porcentaje de avance'),
        default=0,
        validators=[MaxLengthValidator(100)]
    )

    class Meta:
        verbose_name = _('Actividad del Plan Anual')
        verbose_name_plural = _('Actividades del Plan Anual')
        ordering = ['fecha_inicio']

    def clean(self):
        # Validar que las fechas sean coherentes
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError(_('La fecha de inicio no puede ser posterior a la fecha de finalización'))

        # Validar que el responsable pertenezca al mismo nivel organizacional
        if (self.responsable.profile.organizational_level !=
                self.plan.organization_level):
            raise ValidationError(_('El responsable debe pertenecer al mismo nivel organizacional que el plan'))

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"

    class Aprobacion(models.Model):
        ESTADOS = (
            ('P', 'Pendiente'),
            ('A', 'Aprobado'),
            ('R', 'Rechazado')
        )

        actividad = models.ForeignKey(
            'ActividadPlanAnual',
            on_delete=models.CASCADE,
            related_name='aprobaciones'
        )
        aprobador = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.PROTECT,
            related_name='aprobaciones_pendientes'
        )
        estado = models.CharField(
            max_length=1,
            choices=ESTADOS,
            default='P'
        )
        fecha_aprobacion = models.DateTimeField(null=True, blank=True)
        comentarios = models.TextField(blank=True)
        orden = models.PositiveIntegerField()

        class Meta:
            ordering = ['orden']
            unique_together = [['actividad', 'aprobador']]

        def save(self, *args, **kwargs):
            if self.estado in ['A', 'R'] and not self.fecha_aprobacion:
                self.fecha_aprobacion = timezone.now()
                self._enviar_notificacion()
            super().save(*args, **kwargs)

        def _enviar_notificacion(self):
            context = {
                'actividad': self.actividad,
                'aprobador': self.aprobador,
                'estado': self.get_estado_display(),
                'comentarios': self.comentarios,
                'dominio': settings.DOMAIN  # Asegúrate de definir DOMAIN en settings.py
            }

            send_mail(
        subject=f"Actividad {self.get_estado_display()} - {self.actividad.nombre}",
        message=render_to_string('emails/notificacion_aprobacion.txt', context),
        html_message=render_to_string('emails/notificacion_aprobacion.html', context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[self.actividad.responsable.email],
        fail_silently=True
    )

    def __str__(self):
        return f"Aprobación #{self.id} - {self.get_estado_display()}"