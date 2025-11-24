from django.shortcuts import get_object_or_404, render, redirect
from .models import Inventario, Material, Notificacion
from .forms import MaterialForm, MaterialInventarioForm
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

#----------------------------------------------------------------------------------------
# Vistas según roles

@login_required
def tecnico(request):
    return render(request, 'rol/tecnico.html')

@login_required
def bodega(request):
    return render(request, 'rol/bodega.html')

@login_required
def chofer(request):
    return render(request, 'rol/chofer.html')

@login_required
def gerente(request):
    return render(request, 'rol/gerente.html')
#----------------------------------------------------------------------------------------
# Vista Login

def login_view(request):
    if request.user.is_authenticated:
        return redirect('inventario')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirigir a la página que intentaba acceder o al inventario
            next_url = request.GET.get('next', 'inventario')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            
    # Se ejecuta cuando el método es GET (primera vez que cargas la página)
    return render(request, 'general/login.html')
        
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')

#----------------------------------------------------------------------------------------
# Vista según funcionalidad

@login_required
def historial_tecnico(request):
    return render(request, 'funcionalidad/historial_tecnico.html')

@login_required
def solicitud(request):
    return render(request, 'funcionalidad/solicitud.html')

#inventario
@login_required
def inventario(request):
    # Verificar stock crítico cada vez que se cargue el inventario
    #verificar_stock_critico(request.user)
    
    inventario = Inventario.objects.select_related('material').all()
    return render(request, 'funcionalidad/inventario.html', {'inventario': inventario})

@login_required
def detalle_material(request, id):
    material = get_object_or_404(Material, id=id)
    return render(request, 'funcionalidad/inv_detalle_material.html', {'material': material})

@login_required
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
@login_required
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

def marcar_leida(request, id):
    notificacion = get_object_or_404(Notificacion, id=id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    if notificacion.url:
        return redirect(notificacion.url)
    return redirect('inventario')

def marcar_todas_leidas(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect('inventario')
'''
def verificar_stock_critico(usuario):
    """Genera notificaciones para materiales con stock crítico"""
    items_criticos = Inventario.objects.filter(
        stock_actual__lte=models.F('stock_seguridad')
    )
    for item in items_criticos:
        # Evitar duplicados
        if not Notificacion.objects.filter(
            tipo='stock_critico',
            mensaje__contains=item.material.descripcion,
            leida=False
        ).exists():
            Notificacion.objects.create(
                usuario=usuario,
                tipo='stock_critico',
                mensaje=f'Stock crítico: {item.material.descripcion} - Quedan {item.stock_actual} unidades',
                url=f'/material/{item.material.id}/'
            )
'''