from django.shortcuts import get_object_or_404, render, redirect
from .models import Inventario, Material
from .forms import MaterialForm, MaterialInventarioForm

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
    material = get_object_or_404(Material, id=id)
    if request.method == 'POST':
        # Captura datos del formulario
        material.codigo = request.POST.get('codigo')
        material.descripcion = request.POST.get('descripcion')
        material.unidad_medida = request.POST.get('unidad_medida')
        material.categoria = request.POST.get('categoria')
        material.ubicacion = request.POST.get('ubicacion')
        material.save()
        # Luego de guardar, redirige a alguna vista
        return redirect('inventario')
    return render(request, 'funcionalidad/inv_editar_material.html', {'material': material})

'''
def ingreso_material(request):
    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        descripcion = request.POST.get('descripcion')
        unidad_medida = request.POST.get('unidad_medida')
        categoria = request.POST.get('categoria')
        ubicacion = request.POST.get('ubicacion')

        # Validación simple (se puede expandir)
        if codigo and descripcion and unidad_medida and categoria and ubicacion:
            Material.objects.create(
                codigo=codigo,
                descripcion=descripcion,
                unidad_medida=unidad_medida,
                categoria=categoria,
                ubicacion=ubicacion,
            )
            return redirect('inventario')  # O muestra confirmación

        mensaje = 'Todos los campos son obligatorios'
        return render(request, 'funcionalidad/inv_ingreso_material.html',
                      {'mensaje': mensaje})

    return render(request, 'funcionalidad/inv_ingreso_material.html')


def ingreso_material(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('inventario')
    else:
        form = MaterialForm()
    return render(request, 'funcionalidad/inv_ingreso_material.html', {'form': form})
'''
def ingreso_material(request):
    # Calcular código sugerido
    last_material = Material.objects.order_by('-id').first()
    next_id = (last_material.id + 1) if last_material else 1
    codigo_sugerido = f"MAT{next_id:04d}"

    if request.method == 'POST':
        form = MaterialInventarioForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            # Si el usuario no editó el código, queda el sugerido
            if not material.codigo:
                material.codigo = codigo_sugerido
            material.save()
            Inventario.objects.create(
                material=material,
                stock_actual=form.cleaned_data['stock_actual'],
                stock_seguridad=form.cleaned_data['stock_seguridad'],
            )
            return redirect('inventario')
    else:
        # Pre-cargar el código sugerido en el form
        form = MaterialInventarioForm(initial={'codigo': codigo_sugerido})
    return render(request, 'funcionalidad/inv_ingreso_material.html', {'form': form})
