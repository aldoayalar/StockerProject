from django import forms
from .models import Material, Inventario, Solicitud, DetalleSolicitud
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

# Obtener el modelo de Usuario personalizado
User = get_user_model()

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['codigo', 'descripcion', 'unidad_medida', 'categoria', 'ubicacion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unidad_medida': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class MaterialInventarioForm(forms.ModelForm):
    stock_actual = forms.IntegerField(
        min_value=0, 
        required=True, 
        label="Stock Inicial",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    stock_seguridad = forms.IntegerField(
        min_value=0, 
        required=True, 
        label="Stock Crítico",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Material
        fields = ['codigo', 'descripcion', 'unidad_medida', 'categoria', 'ubicacion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),  # ✅ Select
            'categoria': forms.Select(attrs={'class': 'form-select'}),      # ✅ Select
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
        def clean_codigo(self):
            """
            Valida que el código no exista ya en la base de datos
            """
            codigo = self.cleaned_data.get('codigo')
            # Verificar si el código ya existe
            if Material.objects.filter(codigo=codigo).exists():
                raise ValidationError(
                    f'El código "{codigo}" ya está registrado. Por favor usa otro código.'
                )
            
            # Siempre devolver el valor limpio
            return codigo
        
class EditarMaterialForm(forms.ModelForm):
    """
    Formulario para editar un material existente
    """
    class Meta:
        model = Material
        fields = ['codigo', 'descripcion', 'unidad_medida', 'categoria', 'ubicacion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.get('instance').id if kwargs.get('instance') else None
        super().__init__(*args, **kwargs)
    
    def clean_codigo(self):
        """
        Valida que el código no exista, excepto para el material actual
        """
        codigo = self.cleaned_data.get('codigo')
        
        # Verificar si existe otro material con ese código (excluyendo el actual)
        exists = Material.objects.filter(codigo=codigo).exclude(id=self.instance_id).exists()
        
        if exists:
            raise ValidationError(
                f'El código "{codigo}" ya está registrado en otro material. Por favor usa otro código.'
            )
        
        return codigo

        
class SolicitudForm(forms.ModelForm):
    """
    Formulario para la cabecera de la solicitud
    """
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe el motivo de tu solicitud...'
        }),
        label='Motivo de la solicitud'
    )
    
    class Meta:
        model = Solicitud
        fields = ['motivo']
        
class DetalleSolicitudForm(forms.ModelForm):
    """
    Formulario para cada detalle (material) de la solicitud
    """
    material = forms.ModelChoiceField(
        queryset=Material.objects.all().order_by('descripcion'),
        widget=forms.Select(attrs={
            'class': 'form-select material-select',
        }),
        label='Material',
        empty_label='Seleccionar material...'
    )
    
    cantidad = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'placeholder': 'Cantidad'
        }),
        label='Cantidad'
    )
    
    class Meta:
        model = DetalleSolicitud
        fields = ['material', 'cantidad']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar stock disponible en el label del material
        self.fields['material'].label_from_instance = self.material_label_with_stock
    
    @staticmethod
    def material_label_with_stock(obj):
        try:
            stock = obj.inventario.stock_actual
            return f"{obj.descripcion} (Stock: {stock})"
        except:
            return f"{obj.descripcion} (Sin inventario)"
        
# Formset para manejar múltiples detalles
DetalleSolicitudFormSet = inlineformset_factory(
    Solicitud,
    DetalleSolicitud,
    form=DetalleSolicitudForm,
    extra=1,  # Número de formularios vacíos iniciales
    min_num=1,  # Mínimo 1 material
    max_num=10,  # Máximo 10 materiales por solicitud
    validate_min=True,
    validate_max=True,
    can_delete=True
)
        
class FiltroSolicitudesForm(forms.Form):
    """
    Formulario para filtrar solicitudes en el historial
    """
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Fecha desde'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'placeholder': 'Fecha hasta'
        }),
        label='Hasta'
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los estados')] + Solicitud.ESTADO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    material = forms.ModelChoiceField(
        required=False,
        queryset=Material.objects.all().order_by('descripcion'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-placeholder': 'Todos los materiales'
        }),
        label='Material',
        empty_label='Todos los materiales'
    )
    
    solicitante = forms.ModelChoiceField(
        required=False,
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Solicitante',
        empty_label='Todos los usuarios'
    )
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por ID o motivo...'
        }),
        label='Búsqueda'
    )
        
class CambiarPasswordForm(PasswordChangeForm):
    """
    Formulario personalizado para cambiar contraseña
    """
    old_password = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual',
            'autocomplete': 'current-password'
        })
    )
    new_password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu nueva contraseña',
            'autocomplete': 'new-password'
        }),
        help_text='Mínimo 8 caracteres. No puede ser completamente numérica.'
    )
    new_password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirma tu nueva contraseña',
            'autocomplete': 'new-password'
        })
    )

    def clean_new_password2(self):
        """
        Validación personalizada que elimina espacios en blanco
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        # Eliminar espacios en blanco al inicio y final
        if password1:
            password1 = password1.strip()
        if password2:
            password2 = password2.strip()
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    "Las dos contraseñas no coinciden. Verifica que sean exactamente iguales.",
                    code='password_mismatch',
                )
        return password2

    class Meta:
        model = User
        fields = ['old_password', 'new_password1', 'new_password2']
        
