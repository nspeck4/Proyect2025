from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ActividadPlanAnual, Aprobacion


@receiver(post_save, sender=ActividadPlanAnual)
def configurar_flujo_aprobacion(sender, instance, created, **kwargs):
    if created:
        # Obtener la jerarquía de aprobación basada en la organización
        aprobadores = instance.plan.organization_level.get_approvers()

        for orden, aprobador in enumerate(aprobadores, start=1):
            Aprobacion.objects.create(
                actividad=instance,
                aprobador=aprobador,
                orden=orden
            )