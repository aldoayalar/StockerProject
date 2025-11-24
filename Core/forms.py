from django import forms
from .models import Material, Inventario, Solicitud

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
    # Campos adicionales del stock inicial
    stock_actual = forms.IntegerField(min_value=0, required=True, label="Stock Inicial")
    stock_seguridad = forms.IntegerField(min_value=0, required=True, label="Stock Crítico")
    
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
        
class SolicitudForm(forms.ModelForm):
    material = forms.ModelChoiceField(
        queryset=Material.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Selecciona un material"
    )
    
    class Meta:
        model = Solicitud
        fields = ['material', 'cantidad', 'motivo']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'material': 'Material solicitado',
            'cantidad': 'Cantidad',
            'motivo': 'Motivo de la solicitud',
        }