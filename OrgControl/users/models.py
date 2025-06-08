from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class OrganizationLevel(models.Model):
    class LevelType(models.TextChoices):
        CENTRAL = 'CENTRAL', _('Oficina Central')
        ARC = 'ARC', _('Área de Regulación y Control')
        UEB = 'UEB', _('Unidad Empresarial de Base')

    name = models.CharField(
        _('Nombre'),
        max_length=100,
        help_text=_("Nombre descriptivo del nivel organizacional")
    )
    level_type = models.CharField(
        _('Tipo de nivel'),
        max_length=10,
        choices=LevelType.choices,
        help_text=_("Tipo de nivel en la jerarquía organizacional")
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_('Nivel superior'),
        help_text=_("Nivel organizacional al que reporta")
    )
    director = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='directed_levels',
        verbose_name=_('Director a cargo'),
        help_text=_("Usuario responsable de este nivel"),
        limit_choices_to={'profile__position__in': ['DG', 'DIR_ARC', 'DIR_UEB']}
    )

    class Meta:
        verbose_name = _('Nivel Organizacional')
        verbose_name_plural = _('Niveles Organizacionales')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'level_type'],
                name='unique_organization_level_name'
            ),
            models.CheckConstraint(
                check=~models.Q(level_type='CENTRAL') | models.Q(parent__isnull=True),
                name='central_cannot_have_parent'
            )
        ]

    def clean(self):
        # Validación 1: La Oficina Central no puede tener padre
        if self.level_type == self.LevelType.CENTRAL and self.parent is not None:
            raise ValidationError(_('La Oficina Central no puede tener un nivel superior'))

        # Validación 2: ARC y UEB deben reportar a la Oficina Central
        if self.level_type in [self.LevelType.ARC, self.LevelType.UEB] and (
                self.parent is None or self.parent.level_type != self.LevelType.CENTRAL
        ):
            raise ValidationError(_('Las ARC y UEB deben reportar directamente a la Oficina Central'))

        # Validación 3: Coherencia entre tipo de nivel y cargo del director
        position_map = {
            self.LevelType.CENTRAL: 'DG',
            self.LevelType.ARC: 'DIR_ARC',
            self.LevelType.UEB: 'DIR_UEB'
        }
        if hasattr(self.director, 'profile') and self.director.profile.position != position_map[self.level_type]:
            raise ValidationError(_('El director asignado no tiene el cargo adecuado para este nivel'))

    def __str__(self):
        return f"{self.get_level_type_display()}: {self.name}"


class CustomUser(AbstractUser):
    class Position(models.TextChoices):
        DG = 'DG', _('Director General')
        DIR_ARC = 'DIR_ARC', _('Director de ARC')
        DIR_UEB = 'DIR_UEB', _('Director de UEB')
        ESP_ARC = 'ESP_ARC', _('Especialista de ARC')
        ESP_UEB = 'ESP_UEB', _('Especialista de UEB')
        ADMIN = 'ADMIN', _('Administrador del Sistema')

    position = models.CharField(
        _('Cargo'),
        max_length=10,
        choices=Position.choices,
        default=Position.ESP_ARC
    )
    organization_level = models.ForeignKey(
        OrganizationLevel,
        on_delete=models.PROTECT,
        related_name='members',
        verbose_name=_('Nivel Organizacional'),
        null=True,
        blank=True
    )
    boss = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates',
        verbose_name=_('Supervisor Directo')
    )

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['last_name', 'first_name']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(boss=models.F('id')),
                name='user_cannot_be_own_boss'
            )
        ]

    def clean(self):
        # Validación 1: Coherencia cargo-nivel organizacional
        position_level_map = {
            'DG': OrganizationLevel.LevelType.CENTRAL,
            'DIR_ARC': OrganizationLevel.LevelType.ARC,
            'DIR_UEB': OrganizationLevel.LevelType.UEB
        }

        if self.position in position_level_map and (
                self.organization_level is None or
                self.organization_level.level_type != position_level_map[self.position]
        ):
            raise ValidationError(
                _('El cargo %(position)s debe estar asignado a un %(level)s') % {
                    'position': self.get_position_display(),
                    'level': OrganizationLevel.LevelType.labels[position_level_map[self.position]]
                }
            )

        # Validación 2: Especialistas deben tener jefe asignado
        if self.position in ['ESP_ARC', 'ESP_UEB'] and self.boss is None:
            raise ValidationError(_('Los especialistas deben tener un supervisor directo asignado'))

    def get_subordinates(self, include_indirect=True):
        """Obtiene todos los subordinados"""
        subordinates = list(self.subordinates.all())
        if include_indirect:
            for sub in subordinates:
                subordinates += sub.get_subordinates()
        return subordinates

    def get_approvers_for_module(self, module):
        """Obtiene los aprobadores para un módulo específico según jerarquía"""
        from .models import ApprovalFlow
        flow = ApprovalFlow.objects.get(module=module)
        return flow.approvers.filter(
            approverrole__approval_order__gt=0
        ).order_by('approverrole__approval_order')


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    phone = models.CharField(
        _('Teléfono'),
        max_length=15,
        blank=True
    )
    address = models.TextField(
        _('Dirección'),
        blank=True
    )
    profile_picture = models.ImageField(
        _('Foto de Perfil'),
        upload_to='profiles/',
        null=True,
        blank=True
    )
    signature = models.ImageField(
        _('Firma Digital'),
        upload_to='signatures/',
        null=True,
        blank=True,
        help_text=_('Firma escaneada para documentos oficiales')
    )

    class Meta:
        verbose_name = _('Perfil de Usuario')
        verbose_name_plural = _('Perfiles de Usuario')

    def __str__(self):
        return _('Perfil de %(username)s') % {'username': self.user.username}


class ApprovalFlow(models.Model):
    class Module(models.TextChoices):
        ANNUAL_PLAN = 'annual_plan', _('Plan Anual')
        MONTHLY_PLAN = 'monthly_plan', _('Plan Mensual')
        INDIVIDUAL_PLAN = 'individual_plan', _('Plan Individual')
        RISKS = 'risks', _('Gestión de Riesgos')
        NON_CONFORMITY = 'non_conformity', _('No Conformidades')

    module = models.CharField(
        _('Módulo'),
        max_length=20,
        choices=Module.choices,
        unique=True
    )
    approvers = models.ManyToManyField(
        CustomUser,
        through='ApproverRole',
        verbose_name=_('Aprobadores')
    )

    def __str__(self):
        return self.get_module_display()


class ApproverRole(models.Model):
    flow = models.ForeignKey(
        ApprovalFlow,
        on_delete=models.CASCADE,
        verbose_name=_('Flujo')
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_('Usuario')
    )
    role_name = models.CharField(
        _('Nombre del Rol'),
        max_length=100
    )
    approval_order = models.PositiveIntegerField(
        _('Orden de Aprobación'),
        help_text=_('Orden en el que este usuario debe aprobar (1=primero)')
    )

    class Meta:
        verbose_name = _('Rol de Aprobación')
        verbose_name_plural = _('Roles de Aprobación')
        ordering = ['approval_order']
        constraints = [
            models.UniqueConstraint(
                fields=['flow', 'user'],
                name='unique_approver_per_flow'
            ),
            models.UniqueConstraint(
                fields=['flow', 'approval_order'],
                name='unique_order_per_flow'
            )
        ]

    def __str__(self):
        return f"{self.role_name} ({self.user.get_full_name()})"