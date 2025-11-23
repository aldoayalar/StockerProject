from django.shortcuts import get_object_or_404, render
from .models import Inventario, Material

#----------------------------------------------------------------------------------------
# Vistas según roles

def tecnico(request):
    return render(request, 'rol/tecnico.html')

def bodega(request):
    return render(request, 'rol/bodega.html')

def chofer(request):
    return render(request, 'rol/chofer.html')

def gerente(request):
    return render(request, 'rol/gerente.html')
#----------------------------------------------------------------------------------------
# Vista Login

def login(request):
    return render(request, 'general/login.html')

#----------------------------------------------------------------------------------------
# Vista según funcionalidad

def historial_tecnico(request):
    return render(request, 'funcionalidad/historial_tecnico.html')

def solicitud(request):
    return render(request, 'funcionalidad/solicitud.html')

#inventario
def inventario(request):
    inventario = Inventario.objects.select_related('material').all()
    return render(request, 'funcionalidad/inventario.html', {'inventario': inventario})

def detalle_material(request, id):
    material = get_object_or_404(Material, id=id)
    return render(request, 'funcionalidad/inv_detalle_material.html', {'material': material})

def editar_material(request, id):
    material = get_object_or_404(Material, id=id)
    # Si el método es POST, actualizar campos aquí...
    # Si es GET, mostrar el formulario con los datos actuales del material
    return render(request, 'funcionalidad/inv_editar_material.html', {'material': material})
