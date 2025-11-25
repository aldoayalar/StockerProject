from django.shortcuts import get_object_or_404, render, redirect

from django.db import models, transaction
from django.db.models import Sum, Count, Q

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test

from django.utils import timezone

from django.core.paginator import Paginator

from .models import Inventario, Material, Notificacion, Solicitud, DetalleSolicitud
from .forms import MaterialForm, MaterialInventarioForm, SolicitudForm, FiltroSolicitudesForm, CambiarPasswordForm, SolicitudForm, DetalleSolicitudFormSet

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
# ===================================== AUTENTICACIÓN ========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirigir a la página que intentaba acceder o al inventario
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
            
    # Se ejecuta cuando el método es GET (primera vez que cargas la página)
    return render(request, 'general/login.html')
        
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('login')

@login_required
def cambiar_password(request):
    """
    Vista para cambiar la contraseña del usuario actual
    """
    if request.method == 'POST':
        form = CambiarPasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Importante: Actualizar la sesión para que no cierre sesión
            update_session_auth_hash(request, user)
            messages.success(request, '¡Tu contraseña ha sido cambiada exitosamente!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CambiarPasswordForm(user=request.user)
    
    return render(request, 'funcionalidad/cambiar_password.html', {'form': form})



#-------------------------------------------------------------------------------------------------------
# Vista según funcionalidad

@login_required
def historial_tecnico(request):
    return render(request, 'funcionalidad/historial_tecnico.html')

@login_required
def solicitud(request):
    return render(request, 'funcionalidad/solicitud.html')



# ======================================== INVENTARIO =====================================



@login_required
def inventario(request):
    # Verificar stock crítico cada vez que se cargue el inventario
    #verificar_stock_critico(request.user)
    
    inventario = Inventario.objects.select_related('material').all()
    return render(request, 'funcionalidad/inv_inventario.html', {'inventario': inventario})

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



# ============================================= SOLICITUDES DE MATERIALES ====================================

@login_required
def crear_solicitud(request):
    """
    Vista para crear una solicitud con múltiples materiales
    """
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        formset = DetalleSolicitudFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Crear la solicitud
                    solicitud = form.save(commit=False)
                    solicitud.solicitante = request.user
                    solicitud.save()
                    
                    # Asociar el formset a la solicitud y guardar
                    formset.instance = solicitud
                    formset.save()
                    
                    messages.success(
                        request, 
                        f'Solicitud #{solicitud.id} creada exitosamente con {solicitud.total_items()} materiales.'
                    )
                    return redirect('mis_solicitudes')
            except Exception as e:
                messages.error(request, f'Error al crear la solicitud: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = SolicitudForm()
        formset = DetalleSolicitudFormSet()
    
    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'funcionalidad/solmat_crear_solicitud.html', context)

@login_required
def mis_solicitudes(request):
    """
    Vista para listar las solicitudes del usuario actual
    """
    solicitudes = Solicitud.objects.filter(
        solicitante=request.user
    ).prefetch_related('detalles__material').order_by('-fecha_solicitud')
    
    context = {
        'solicitudes': solicitudes,
    }
    return render(request, 'funcionalidad/mis_solicitudes.html', context)

@login_required
def detalle_solicitud(request, solicitud_id):
    """
    Vista para ver el detalle completo de una solicitud
    """
    solicitud = get_object_or_404(
        Solicitud.objects.prefetch_related('detalles__material'),
        id=solicitud_id
    )
    
    # Verificar permisos (solo el solicitante o staff puede ver)
    if solicitud.solicitante != request.user and not request.user.is_staff:
        messages.error(request, 'No tienes permiso para ver esta solicitud.')
        return redirect('mis_solicitudes')
    
    context = {
        'solicitud': solicitud,
    }
    return render(request, 'funcionalidad/solmat_detalle_solicitud.html', context)

def es_staff(user):
    return user.is_staff

@login_required
@user_passes_test(es_staff)
def gestionar_solicitudes(request):
    """
    Vista para que staff/bodega gestione todas las solicitudes
    """
    solicitudes_pendientes = Solicitud.objects.filter(
        estado='pendiente'
    ).prefetch_related('detalles__material').order_by('-fecha_solicitud')
    
    todas_solicitudes = Solicitud.objects.all().prefetch_related(
        'detalles__material'
    ).order_by('-fecha_solicitud')[:20]
    
    context = {
        'solicitudes_pendientes': solicitudes_pendientes,
        'todas_solicitudes': todas_solicitudes,
    }
    return render(request, 'funcionalidad/solmat_gestionar.html', context)

@login_required
@user_passes_test(es_staff)
def aprobar_solicitud(request, solicitud_id):
    """
    Aprobar una solicitud
    """
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    
    if request.method == 'POST':
        solicitud.estado = 'aprobada'
        solicitud.respondido_por = request.user
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        
        messages.success(request, f'Solicitud #{solicitud.id} aprobada exitosamente.')
        return redirect('gestionar_solicitudes')
    
    return redirect('detalle_solicitud', solicitud_id=solicitud_id)

@login_required
@user_passes_test(es_staff)
def rechazar_solicitud(request, solicitud_id):
    """
    Rechazar una solicitud
    """
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        solicitud.estado = 'rechazada'
        solicitud.respondido_por = request.user
        solicitud.fecha_respuesta = timezone.now()
        solicitud.observaciones = observaciones
        solicitud.save()
        
        messages.warning(request, f'Solicitud #{solicitud.id} rechazada.')
        return redirect('gestionar_solicitudes')
    
    return redirect('detalle_solicitud', solicitud_id=solicitud_id)

@login_required
def cancelar_solicitud(request, solicitud_id):
    """
    Cancelar una solicitud propia (solo si está pendiente)
    """
    solicitud = get_object_or_404(Solicitud, id=solicitud_id, solicitante=request.user)
    
    if solicitud.estado == 'pendiente' and request.method == 'POST':
        solicitud.delete()
        messages.info(request, 'Solicitud cancelada exitosamente.')
        return redirect('mis_solicitudes')
    
    messages.error(request, 'No se puede cancelar esta solicitud.')
    return redirect('detalle_solicitud', solicitud_id=solicitud_id)



@login_required
def historial_solicitudes(request):
    """
    Vista del historial de solicitudes con filtros
    """
    # Obtener todas las solicitudes (staff ve todas, usuarios solo las suyas)
    if request.user.is_staff:
        solicitudes = Solicitud.objects.all()
    else:
        solicitudes = Solicitud.objects.filter(solicitante=request.user)
    
    # Aplicar filtros si se envió el formulario
    form = FiltroSolicitudesForm(request.GET or None)
    
    if form.is_valid():
        # Filtro por fecha desde
        fecha_desde = form.cleaned_data.get('fecha_desde')
        if fecha_desde:
            solicitudes = solicitudes.filter(fecha_solicitud__date__gte=fecha_desde)
        
        # Filtro por fecha hasta
        fecha_hasta = form.cleaned_data.get('fecha_hasta')
        if fecha_hasta:
            solicitudes = solicitudes.filter(fecha_solicitud__date__lte=fecha_hasta)
        
        # Filtro por estado
        estado = form.cleaned_data.get('estado')
        if estado:
            solicitudes = solicitudes.filter(estado=estado)
        
        # Filtro por material
        material = form.cleaned_data.get('material')
        if material:
            solicitudes = solicitudes.filter(material=material)
        
        # Filtro por solicitante (solo para staff)
        if request.user.is_staff:
            solicitante = form.cleaned_data.get('solicitante')
            if solicitante:
                solicitudes = solicitudes.filter(solicitante=solicitante)
        
        # Búsqueda por texto
        buscar = form.cleaned_data.get('buscar')
        if buscar:
            solicitudes = solicitudes.filter(
                Q(id__icontains=buscar) | 
                Q(motivo__icontains=buscar) |
                Q(observaciones__icontains=buscar)
            )
    
    # Ordenar por fecha (más recientes primero)
    solicitudes = solicitudes.select_related(
        'solicitante', 'material', 'respondido_por'
    ).order_by('-fecha_solicitud')
    
    # Paginación (15 por página)
    paginator = Paginator(solicitudes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas del filtro actual
    stats = {
        'total': solicitudes.count(),
        'pendientes': solicitudes.filter(estado='pendiente').count(),
        'aprobadas': solicitudes.filter(estado='aprobada').count(),
        'rechazadas': solicitudes.filter(estado='rechazada').count(),
    }
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'solicitudes': page_obj,
        'stats': stats,
    }
    
    return render(request, 'funcionalidad/solmat_historial.html', context)


# ====================================== NOTIFICACIONES ============================================

@login_required
def marcar_leida(request, id):
    notificacion = get_object_or_404(Notificacion, id=id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    if notificacion.url:
        return redirect(notificacion.url)
    return redirect('inventario')

@login_required
def marcar_todas_leidas(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect('inventario')


# ============================================= DASHBOARD ===============================================

@login_required
def dashboard(request):
    # KPIs generales
    total_materiales = Material.objects.count()
    total_usuarios = User.objects.filter(is_active=True).count()
    
    # Solicitudes
    solicitudes_pendientes = Solicitud.objects.filter(estado='pendiente').count()
    solicitudes_aprobadas = Solicitud.objects.filter(estado='aprobada').count()
    solicitudes_rechazadas = Solicitud.objects.filter(estado='rechazada').count()
    
    # Inventario
    materiales_criticos = Inventario.objects.filter(
        stock_actual__lte=models.F('stock_seguridad')
    ).count()
    
    stock_total = Inventario.objects.aggregate(
        total=Sum('stock_actual')
    )['total'] or 0
    
    # Solicitudes recientes (últimas 5)
    solicitudes_recientes = Solicitud.objects.select_related(
        'solicitante', 'material'
    ).order_by('-fecha_solicitud')[:5]
    
    context = {
        'total_materiales': total_materiales,
        'total_usuarios': total_usuarios,
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
        'materiales_criticos': materiales_criticos,
        'stock_total': stock_total,
        'solicitudes_recientes': solicitudes_recientes,
    }
    
    return render(request, 'funcionalidad/dashboard.html', context)