from django import forms
from .models import Material, Inventario, Solicitud, DetalleSolicitud, Local, Usuario
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
            'unidad_medida': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
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
            'unidad_medida': forms.Select(attrs={'class': 'form-select'}),  
            'categoria': forms.Select(attrs={'class': 'form-select'}),      
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
    
class CargaMasivaStockForm(forms.Form):
    archivo = forms.FileField(label="Archivo Excel")
    modo = forms.ChoiceField(
        choices=[
            ('entrada', 'Sumar al stock actual (entrada)'),
            ('ajuste', 'Reemplazar stock (ajuste)'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
class LocalForm(forms.ModelForm):
    #crear/editar locales
    class Meta:
        model = Local
        fields = ['codigo', 'nombre', 'direccion', 'numero', 'comuna', 'region']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: LOC001'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del local'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Calle'
            }),
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número (opcional)'
            }),
            'comuna': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Comuna'
            }),
            'region': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Región'
            }),
        }

        
class SolicitudForm(forms.ModelForm):

    motivo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe el motivo de tu solicitud...'
        }),
        label='Motivo de la solicitud'
    )
    
    local_destino = forms.ModelChoiceField(
        queryset=Local.objects.all().order_by('codigo'), 
        empty_label="Seleccione una sucursal...",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'select-local' # 
        }),
        label='Sucursal / Local de destino'
    )

    class Meta:
        model = Solicitud
        fields = ['local_destino', 'motivo']

        
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
        max_value=10,  
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 10,  
            'placeholder': 'Cantidad (máx. 10)'
        }),
        label='Cantidad',
        error_messages={
            'max_value': 'No puedes solicitar más de 10 unidades de este material.',
            'min_value': 'Debes solicitar al menos 1 unidad.',
        }
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


DetalleSolicitudFormSet = inlineformset_factory(
    Solicitud,
    DetalleSolicitud,
    form=DetalleSolicitudForm,
    extra=1,
    min_num=1,
    max_num=10,
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
        
class UsuarioForm(forms.ModelForm):
    """Formulario para crear/editar usuarios (solo GERENCIA)"""
    password = forms.CharField(
        required=False,
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para no cambiar (solo edición)'
        }),
        help_text='Mínimo 8 caracteres. Dejar vacío al editar si no quieres cambiar la contraseña.'
    )
    
    confirmar_password = forms.CharField(
        required=False,
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'rol', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'rol': 'Rol',
            'is_active': 'Usuario activo'
        }
    
    def __init__(self, *args, **kwargs):
        self.is_new = kwargs.pop('is_new', False)
        super().__init__(*args, **kwargs)
        
        # Si es nuevo usuario, la contraseña es obligatoria
        if self.is_new:
            self.fields['password'].required = True
            self.fields['confirmar_password'].required = True
            self.fields['password'].help_text = 'Mínimo 8 caracteres.'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        
        # Verificar si existe otro usuario con ese username
        if self.instance.pk:  # Editando
            if Usuario.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este nombre de usuario ya está en uso.')
        else:  # Creando nuevo
            if Usuario.objects.filter(username=username).exists():
                raise ValidationError('Este nombre de usuario ya está en uso.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        
        # Verificar si existe otro usuario con ese email
        if self.instance.pk:  # Editando
            if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Este correo electrónico ya está en uso.')
        else:  # Creando nuevo
            if Usuario.objects.filter(email=email).exists():
                raise ValidationError('Este correo electrónico ya está en uso.')
        
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar_password = cleaned_data.get('confirmar_password')
        
        # Validar contraseñas
        if password or confirmar_password:
            if password != confirmar_password:
                raise ValidationError('Las contraseñas no coinciden.')
            
            if len(password) < 8:
                raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        
        # Si es nuevo usuario y no hay contraseña
        if self.is_new and not password:
            raise ValidationError('Debes ingresar una contraseña para el nuevo usuario.')
        
        return cleaned_data
    
    def save(self, commit=True):
        usuario = super().save(commit=False)
        password = self.cleaned_data.get('password')
        
        
        if password:
            usuario.set_password(password)
        
        if commit:
            usuario.save()
        
        return usuario
