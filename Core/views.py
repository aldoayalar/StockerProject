import json

from django.shortcuts import get_object_or_404, render, redirect

from django.db import models, transaction
from django.db.models import Avg, Sum, Count, Q, F
from django.db.models.functions import TruncDate

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test

from django.utils import timezone

from django.core.paginator import Paginator

from .models import Inventario, Material, Notificacion, Solicitud, DetalleSolicitud, Movimiento, Usuario, Alerta, MLResult
from .forms import MaterialForm, MaterialInventarioForm, SolicitudForm, FiltroSolicitudesForm, CambiarPasswordForm, SolicitudForm, DetalleSolicitudFormSet, EditarMaterialForm

from django.http import JsonResponse

from datetime import timedelta

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


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
    # Limpiar todos los mensajes pendientes antes de cerrar sesión
    storage = messages.get_messages(request)
    storage.used = True
    
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
    
    # Obtener todos los registros del inventario con sus materiales
    inventario = Inventario.objects.select_related('material').all()

    # Agregar el promedio de stock crítico calculado por ML
    for item in inventario:
        promedio_ml = MLResult.objects.filter(
            material=item.material
        ).aggregate(
            promedio=Avg('stock_min_calculado')
        )['promedio']
        
        # Agregar como atributo temporal
        item.stock_critico_promedio = round(promedio_ml) if promedio_ml else None
    
    return render(request, 'funcionalidad/inv_inventario.html', {'inventario': inventario})

@login_required
def detalle_material(request, id):
    material = get_object_or_404(Material, id=id)
    return render(request, 'funcionalidad/inv_detalle_material.html', {'material': material})

@login_required
def editar_material(request, id):
    material = get_object_or_404(Material, id=id)
    
    if request.method == 'POST':
        form = EditarMaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Material {material.codigo} actualizado exitosamente.')
            return redirect('inventario')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = EditarMaterialForm(instance=material)
    
    return render(request, 'funcionalidad/inv_editar_material.html', {
        'form': form,
        'material': material
    })



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
    return render(request, 'funcionalidad/solmat_mis_solicitudes.html', context)

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
@user_passes_test(es_staff)
def despachar_solicitud(request, solicitud_id):
    """
    Marcar una solicitud aprobada como despachada y descontar stock
    """
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    
    if solicitud.estado != 'aprobada':
        messages.error(request, 'Solo se pueden despachar solicitudes aprobadas.')
        return redirect('gestionar_solicitudes')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Descontar stock de cada material
                for detalle in solicitud.detalles.all():
                    try:
                        inventario = detalle.material.inventario
                        
                        # Verificar stock suficiente
                        if inventario.stock_actual < detalle.cantidad:
                            messages.error(
                                request, 
                                f'Stock insuficiente para {detalle.material.descripcion}. '
                                f'Disponible: {inventario.stock_actual}, Solicitado: {detalle.cantidad}'
                            )
                            return redirect('detalle_solicitud', solicitud_id=solicitud_id)
                        
                        # Descontar stock
                        stock_anterior = inventario.stock_actual
                        inventario.stock_actual -= detalle.cantidad
                        inventario.save()
                        
                        # Registrar movimiento de salida
                        try:
                            usuario_movimiento = Usuario.objects.get(email=request.user.email)
                        except Usuario.DoesNotExist:
                            # Si no existe en Usuario, crear el movimiento sin ese campo o manejarlo diferente
                            usuario_movimiento = None
                        
                        if usuario_movimiento:
                            Movimiento.objects.create(
                                material=detalle.material,
                                usuario=usuario_movimiento,
                                solicitud=solicitud,
                                tipo='salida',
                                cantidad=detalle.cantidad,
                                detalle=f'Despacho solicitud #{solicitud.id} - {solicitud.motivo}'
                            )
                        
                    except Inventario.DoesNotExist:
                        messages.error(
                            request, 
                            f'El material {detalle.material.codigo} no tiene inventario asociado.'
                        )
                        return redirect('detalle_solicitud', solicitud_id=solicitud_id)
                
                # Actualizar estado de la solicitud
                solicitud.estado = 'despachada'
                solicitud.save()
                
                messages.success(
                    request, 
                    f'Solicitud #{solicitud.id} despachada exitosamente. Stock actualizado.'
                )
                return redirect('gestionar_solicitudes')
                
        except Exception as e:
            messages.error(request, f'Error al despachar solicitud: {str(e)}')
            return redirect('detalle_solicitud', solicitud_id=solicitud_id)
    
    # Si es GET, mostrar confirmación
    context = {
        'solicitud': solicitud,
    }
    return render(request, 'funcionalidad/solmat_confirmar_despacho.html', context)



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
            solicitudes = solicitudes.filter(detalles__material=material).distinct()

        
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
        'solicitante', 'respondido_por'
    ).prefetch_related('detalles__material').order_by('-fecha_solicitud')

    
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

# ============================================= Registro de movimientos ====================================

@login_required
@user_passes_test(es_staff)
def registrar_entrada(request, material_id):
    """
    Registrar entrada manual de material
    """
    material = get_object_or_404(Material, id=material_id)
    
    try:
        inventario = material.inventario
    except Inventario.DoesNotExist:
        messages.error(request, 'Este material no tiene inventario asociado.')
        return redirect('inventario')
    
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 0))
        detalle = request.POST.get('detalle', '')
        
        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
        else:
            try:
                with transaction.atomic():
                    stock_anterior = inventario.stock_actual
                    stock_nuevo = stock_anterior + cantidad
                    
                    # Actualizar inventario
                    inventario.stock_actual = stock_nuevo
                    inventario.save()
                    
                    # Buscar usuario en modelo Usuario personalizado
                    try:
                        usuario_movimiento = Usuario.objects.get(
                            email=request.user.email
                        )
                    except Usuario.DoesNotExist:
                        messages.error(request, 'Tu usuario no está registrado en el sistema de personal.')
                        return redirect('detalle_material', id=material_id)
                    
                    # Crear movimiento
                    Movimiento.objects.create(
                        material=material,
                        usuario=usuario_movimiento,
                        tipo='entrada',
                        cantidad=cantidad,
                        detalle=detalle or f'Entrada manual registrada por {request.user.username}'
                    )
                    
                    messages.success(
                        request, 
                        f'Entrada registrada: +{cantidad} {material.unidad_medida}. Stock actual: {stock_nuevo}'
                    )
                    return redirect('detalle_material', id=material_id)
                    
            except Exception as e:
                messages.error(request, f'Error al registrar entrada: {str(e)}')
    
    context = {
        'material': material,
        'inventario': inventario,
    }
    return render(request, 'funcionalidad/mov_registrar_entrada.html', context)


@login_required
@user_passes_test(es_staff)
def registrar_salida(request, material_id):
    """
    Registrar salida manual de material
    """
    material = get_object_or_404(Material, id=material_id)
    
    try:
        inventario = material.inventario
    except Inventario.DoesNotExist:
        messages.error(request, 'Este material no tiene inventario asociado.')
        return redirect('inventario')
    
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 0))
        detalle = request.POST.get('detalle', '')
        
        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
        elif cantidad > inventario.stock_actual:
            messages.error(request, f'Stock insuficiente. Disponible: {inventario.stock_actual}')
        else:
            try:
                with transaction.atomic():
                    stock_anterior = inventario.stock_actual
                    stock_nuevo = stock_anterior - cantidad
                    
                    # Actualizar inventario
                    inventario.stock_actual = stock_nuevo
                    inventario.save()
                    
                    # Buscar usuario en modelo Usuario personalizado
                    try:
                        usuario_movimiento = Usuario.objects.get(
                            email=request.user.email
                        )
                    except Usuario.DoesNotExist:
                        messages.error(request, 'Tu usuario no está registrado en el sistema de personal.')
                        return redirect('detalle_material', id=material_id)
                    
                    # Crear movimiento
                    Movimiento.objects.create(
                        material=material,
                        usuario=usuario_movimiento,
                        tipo='salida',
                        cantidad=cantidad,
                        detalle=detalle or f'Salida manual registrada por {request.user.username}'
                    )
                    
                    messages.success(
                        request, 
                        f'Salida registrada: -{cantidad} {material.unidad_medida}. Stock actual: {stock_nuevo}'
                    )
                    return redirect('detalle_material', id=material_id)
                    
            except Exception as e:
                messages.error(request, f'Error al registrar salida: {str(e)}')
    
    context = {
        'material': material,
        'inventario': inventario,
    }
    return render(request, 'funcionalidad/mov_registrar_salida.html', context)


@login_required
@user_passes_test(es_staff)
def ajustar_inventario(request, material_id):
    """
    Ajustar inventario (correcciones)
    """
    material = get_object_or_404(Material, id=material_id)
    
    try:
        inventario = material.inventario
    except Inventario.DoesNotExist:
        messages.error(request, 'Este material no tiene inventario asociado.')
        return redirect('inventario')
    
    if request.method == 'POST':
        nuevo_stock = int(request.POST.get('nuevo_stock', 0))
        detalle = request.POST.get('detalle', '')
        
        if nuevo_stock < 0:
            messages.error(request, 'El stock no puede ser negativo.')
        else:
            try:
                with transaction.atomic():
                    stock_anterior = inventario.stock_actual
                    diferencia = nuevo_stock - stock_anterior
                    
                    # Actualizar inventario
                    inventario.stock_actual = nuevo_stock
                    inventario.save()
                    
                    # Buscar usuario en modelo Usuario personalizado
                    try:
                        usuario_movimiento = Usuario.objects.get(
                            email=request.user.email
                        )
                    except Usuario.DoesNotExist:
                        messages.error(request, 'Tu usuario no está registrado en el sistema de personal.')
                        return redirect('detalle_material', id=material_id)
                    
                    # Crear movimiento
                    Movimiento.objects.create(
                        material=material,
                        usuario=usuario_movimiento,
                        tipo='ajuste',
                        cantidad=abs(diferencia),
                        detalle=f'Ajuste de inventario ({diferencia:+d}): {detalle}'
                    )
                    
                    messages.success(
                        request, 
                        f'Inventario ajustado. Stock anterior: {stock_anterior}, Stock nuevo: {nuevo_stock}'
                    )
                    return redirect('detalle_material', id=material_id)
                    
            except Exception as e:
                messages.error(request, f'Error al ajustar inventario: {str(e)}')
    
    context = {
        'material': material,
        'inventario': inventario,
    }
    return render(request, 'funcionalidad/mov_ajustar_inventario.html', context)


@login_required
def historial_movimientos(request, material_id):
    """
    Ver historial de movimientos de un material
    """
    material = get_object_or_404(Material, id=material_id)
    movimientos = Movimiento.objects.filter(
        material=material
    ).select_related('usuario').order_by('-fecha')
    
    context = {
        'material': material,
        'movimientos': movimientos,
    }
    return render(request, 'funcionalidad/mov_historial.html', context)

@login_required
@user_passes_test(es_staff)
def historial_movimientos_global(request):
    """
    Historial completo de todos los movimientos del sistema
    """
    movimientos = Movimiento.objects.select_related(
        'material', 'usuario'
    ).all()
    
    # Filtros opcionales
    tipo_filtro = request.GET.get('tipo')
    if tipo_filtro:
        movimientos = movimientos.filter(tipo=tipo_filtro)
    
    fecha_desde = request.GET.get('fecha_desde')
    if fecha_desde:
        movimientos = movimientos.filter(fecha__date__gte=fecha_desde)
    
    fecha_hasta = request.GET.get('fecha_hasta')
    if fecha_hasta:
        movimientos = movimientos.filter(fecha__date__lte=fecha_hasta)
    
    # Ordenar por fecha descendente
    movimientos = movimientos.order_by('-fecha')
    
    # Paginación
    paginator = Paginator(movimientos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'movimientos': page_obj,
        'page_obj': page_obj,
        'tipo_filtro': tipo_filtro,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'funcionalidad/mov_historial_global.html', context)


# ====================================== NOTIFICACIONES ============================================

@login_required
def mis_notificaciones(request):
    """
    Vista para ver todas las notificaciones del usuario
    """
    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).order_by('-creada_en')
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(notificaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notificaciones': page_obj,
        'no_leidas': notificaciones.filter(leida=False).count()
    }
    return render(request, 'funcionalidad/notificaciones.html', context)


@login_required
def marcar_leida(request, id):
    """
    Marcar una notificación como leída
    """
    notificacion = get_object_or_404(Notificacion, id=id, usuario=request.user)
    notificacion.leida = True
    notificacion.save()
    
    # Si tiene URL, redirigir ahí
    if notificacion.url:
        return redirect(notificacion.url)
    return redirect('mis_notificaciones')


@login_required
def marcar_todas_leidas(request):
    """
    Marcar todas las notificaciones como leídas
    """
    if request.method == 'POST':
        Notificacion.objects.filter(
            usuario=request.user, 
            leida=False
        ).update(leida=True)
        messages.success(request, 'Todas las notificaciones han sido marcadas como leídas.')
    
    return redirect('mis_notificaciones')


@login_required
def eliminar_notificacion(request, id):
    """
    Eliminar una notificación
    """
    notificacion = get_object_or_404(Notificacion, id=id, usuario=request.user)
    notificacion.delete()
    messages.success(request, 'Notificación eliminada.')
    return redirect('mis_notificaciones')


@login_required
def obtener_notificaciones_json(request):
    """
    API para obtener notificaciones no leídas (AJAX)
    """
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).order_by('-creada_en')[:10]
    
    data = {
        'count': notificaciones.count(),
        'notificaciones': [
            {
                'id': n.id,
                'tipo': n.tipo,
                'mensaje': n.mensaje,
                'url': n.url or '#',
                'fecha': n.creada_en.strftime('%d/%m/%Y %H:%M'),
                'icono': get_icono_notificacion(n.tipo)
            }
            for n in notificaciones
        ]
    }
    return JsonResponse(data)


def get_icono_notificacion(tipo):
    """
    Retorna el ícono FontAwesome según el tipo de notificación
    """
    iconos = {
        'stock_critico': 'fa-exclamation-triangle',
        'solicitud_pendiente': 'fa-clipboard-list',
        'material_nuevo': 'fa-box',
        'aprobacion': 'fa-check-circle',
    }
    return iconos.get(tipo, 'fa-bell')


@login_required
@user_passes_test(es_staff)
def verificar_alertas_stock(request):
    """
    Verifica materiales en stock crítico y genera alertas
    """
    # Materiales con stock actual <= stock crítico dinámico
    materiales_criticos = Inventario.objects.filter(
        stock_actual__lte=F('stock_min_dinamico')
    ).select_related('material')
    
    alertas_generadas = 0
    
    for inventario in materiales_criticos:
        # Verificar si ya existe una alerta activa para este material
        alerta_existente = Alerta.objects.filter(
            material=inventario.material,
            atendida=False
        ).exists()
        
        if not alerta_existente:
            # Calcular severidad
            porcentaje = (inventario.stock_actual / inventario.stock_min_dinamico * 100) if inventario.stock_min_dinamico > 0 else 0
            
            if porcentaje <= 30:
                severidad = 'alta'
            elif porcentaje <= 60:
                severidad = 'media'
            else:
                severidad = 'baja'
            
            # Crear alerta
            alerta = Alerta.objects.create(
                material=inventario.material,
                umbral_dinamico=inventario.stock_min_dinamico,
                stock_actual=inventario.stock_actual,
                severidad=severidad,
                atendida=False
            )
            
            # Crear notificaciones para bodega y gerencia
            usuarios_notificar = User.objects.filter(
                is_staff=True, 
                is_active=True
            )
            
            for usuario in usuarios_notificar:
                Notificacion.objects.create(
                    alerta=alerta,
                    usuario=usuario,
                    canal='in-app',
                    estado='enviada'
                )
            
            alertas_generadas += 1
    
    messages.success(request, f'{alertas_generadas} alertas generadas.')
    return redirect('dashboard')

# ============================================= DASHBOARD ===============================================

@login_required
def dashboard(request):
    """
    Dashboard principal con estadísticas y gráficos
    """
    # ==================== KPIs GENERALES ====================
    total_materiales = Material.objects.count()
    total_usuarios = User.objects.filter(is_active=True).count()
    
    # Solicitudes
    solicitudes_pendientes = Solicitud.objects.filter(estado='pendiente').count()
    solicitudes_aprobadas = Solicitud.objects.filter(estado='aprobada').count()
    solicitudes_rechazadas = Solicitud.objects.filter(estado='rechazada').count()
    solicitudes_totales = Solicitud.objects.count()
    
    # Inventario
    materiales_criticos = Inventario.objects.filter(
        stock_actual__lte=F('stock_seguridad')
    ).count()
    
    stock_total = Inventario.objects.aggregate(
        total=Sum('stock_actual')
    )['total'] or 0
    
    # ==================== GRÁFICO 1: MATERIALES POR CATEGORÍA ====================
    materiales_por_categoria = Material.objects.values('categoria').annotate(
        total=Count('id')
    ).order_by('-total')
    
    categorias_labels = [item['categoria'] for item in materiales_por_categoria]
    categorias_data = [item['total'] for item in materiales_por_categoria]
    
    # ==================== GRÁFICO 2: SOLICITUDES POR ESTADO ====================
    solicitudes_stats = {
        'labels': ['Pendientes', 'Aprobadas', 'Rechazadas', 'Despachadas'],
        'data': [
            Solicitud.objects.filter(estado='pendiente').count(),
            Solicitud.objects.filter(estado='aprobada').count(),
            Solicitud.objects.filter(estado='rechazada').count(),
            Solicitud.objects.filter(estado='despachada').count(),
        ]
    }
    
    # ==================== GRÁFICO 3: MOVIMIENTOS ÚLTIMOS 7 DÍAS ====================
    hace_7_dias = timezone.now() - timedelta(days=7)
    movimientos_recientes = Movimiento.objects.filter(
        fecha__gte=hace_7_dias
    ).annotate(
        fecha_corta=TruncDate('fecha')
    ).values('fecha_corta', 'tipo').annotate(
        total=Count('id')
    ).order_by('fecha_corta')
    
    # Preparar datos para el gráfico de líneas
    fechas_set = set()
    for mov in movimientos_recientes:
        fechas_set.add(mov['fecha_corta'])
    
    fechas_ordenadas = sorted(list(fechas_set))
    fechas_labels = [fecha.strftime('%d/%m') for fecha in fechas_ordenadas]
    
    entradas_data = []
    salidas_data = []
    
    for fecha in fechas_ordenadas:
        entradas = sum(m['total'] for m in movimientos_recientes 
                      if m['fecha_corta'] == fecha and m['tipo'] == 'entrada')
        salidas = sum(m['total'] for m in movimientos_recientes 
                     if m['fecha_corta'] == fecha and m['tipo'] == 'salida')
        entradas_data.append(entradas)
        salidas_data.append(salidas)
    
    # ==================== TOP 5 MATERIALES MÁS SOLICITADOS ====================
    top_materiales = DetalleSolicitud.objects.values(
        'material__descripcion', 'material__codigo'
    ).annotate(
        total_solicitado=Sum('cantidad')
    ).order_by('-total_solicitado')[:5]
    
    # ==================== MATERIALES EN STOCK CRÍTICO ====================
    materiales_criticos_lista = Inventario.objects.filter(
        stock_actual__lte=F('stock_seguridad')
    ).select_related('material').order_by('stock_actual')[:5]
    
    # ==================== SOLICITUDES RECIENTES ====================
    solicitudes_recientes = Solicitud.objects.select_related(
        'solicitante'
    ).prefetch_related('detalles__material').order_by('-fecha_solicitud')[:5]
    
    # ==================== ACTIVIDAD RECIENTE (MOVIMIENTOS) ====================
    actividad_reciente = Movimiento.objects.select_related(
        'material', 'usuario'
    ).order_by('-fecha')[:10]
    
    context = {
        # KPIs
        'total_materiales': total_materiales,
        'total_usuarios': total_usuarios,
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_aprobadas': solicitudes_aprobadas,
        'solicitudes_rechazadas': solicitudes_rechazadas,
        'solicitudes_totales': solicitudes_totales,
        'materiales_criticos': materiales_criticos,
        'stock_total': stock_total,
        
        # Gráficos (convertir a JSON)
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_data': json.dumps(categorias_data),
        'solicitudes_labels': json.dumps(solicitudes_stats['labels']),
        'solicitudes_data': json.dumps(solicitudes_stats['data']),
        'movimientos_fechas': json.dumps(fechas_labels),
        'movimientos_entradas': json.dumps(entradas_data),
        'movimientos_salidas': json.dumps(salidas_data),
        
        # Listas
        'top_materiales': top_materiales,
        'materiales_criticos_lista': materiales_criticos_lista,
        'solicitudes_recientes': solicitudes_recientes,
        'actividad_reciente': actividad_reciente,
    }
    
    return render(request, 'funcionalidad/dashboard.html', context)


# ==================== EXPORTACIÓN A EXCEL ====================

def crear_estilo_header():
    """
    Estilo para los headers de las tablas Excel
    """
    return {
        'font': Font(bold=True, color='FFFFFF', size=12),
        'fill': PatternFill(start_color='366092', end_color='366092', fill_type='solid'),
        'alignment': Alignment(horizontal='center', vertical='center'),
        'border': Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    }

def aplicar_estilo_celda(celda, estilo):
    """
    Aplica un estilo a una celda
    """
    if 'font' in estilo:
        celda.font = estilo['font']
    if 'fill' in estilo:
        celda.fill = estilo['fill']
    if 'alignment' in estilo:
        celda.alignment = estilo['alignment']
    if 'border' in estilo:
        celda.border = estilo['border']

@login_required
def exportar_inventario_excel(request):
    """
    Exportar inventario completo a Excel
    """
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    
    # Headers
    headers = ['Código', 'Descripción', 'Categoría', 'Unidad de Medida', 
               'Stock Actual', 'Stock Seguridad', 'Estado', 'Ubicación', 'Fecha Creación']
    
    estilo_header = crear_estilo_header()
    
    # Escribir headers
    for col_num, header in enumerate(headers, 1):
        celda = ws.cell(row=1, column=col_num, value=header)
        aplicar_estilo_celda(celda, estilo_header)
    
    # Obtener datos
    inventario = Inventario.objects.select_related('material').all()
    
    # Escribir datos
    for row_num, inv in enumerate(inventario, 2):
        material = inv.material
        
        # Determinar estado
        if inv.stock_actual <= inv.stock_seguridad:
            estado = 'CRÍTICO'
            fill_color = 'FFCCCC'  # Rojo claro
        elif inv.stock_actual <= inv.stock_seguridad * 1.5:
            estado = 'BAJO'
            fill_color = 'FFFFCC'  # Amarillo claro
        else:
            estado = 'NORMAL'
            fill_color = 'CCFFCC'  # Verde claro
        
        # Datos de la fila
        fila_datos = [
            material.codigo,
            material.descripcion,
            material.get_categoria_display(),
            material.get_unidad_medida_display(),
            inv.stock_actual,
            inv.stock_seguridad,
            estado,
            material.ubicacion or 'No especificada',
            material.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        ]
        
        for col_num, valor in enumerate(fila_datos, 1):
            celda = ws.cell(row=row_num, column=col_num, value=valor)
            
            # Aplicar color según estado
            if col_num == 7:  # Columna Estado
                celda.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
                celda.font = Font(bold=True)
            
            # Alineación
            if col_num in [5, 6]:  # Columnas numéricas
                celda.alignment = Alignment(horizontal='right')
            else:
                celda.alignment = Alignment(horizontal='left')
    
    # Ajustar ancho de columnas
    for col_num in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_num)].width = 18
    
    # Preparar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=inventario_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


@login_required
def exportar_solicitudes_excel(request):
    """
    Exportar solicitudes a Excel
    """
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Solicitudes"
    
    # Headers
    headers = ['ID', 'Fecha', 'Solicitante', 'Estado', 'Total Items', 
               'Cantidad Total', 'Respondido Por', 'Fecha Respuesta', 'Motivo']
    
    estilo_header = crear_estilo_header()
    
    # Escribir headers
    for col_num, header in enumerate(headers, 1):
        celda = ws.cell(row=1, column=col_num, value=header)
        aplicar_estilo_celda(celda, estilo_header)
    
    # Obtener datos (últimos 3 meses)
    hace_3_meses = timezone.now() - timedelta(days=90)
    solicitudes = Solicitud.objects.filter(
        fecha_solicitud__gte=hace_3_meses
    ).select_related('solicitante', 'respondido_por').prefetch_related('detalles').order_by('-fecha_solicitud')
    
    # Escribir datos
    for row_num, solicitud in enumerate(solicitudes, 2):
        # Color según estado
        if solicitud.estado == 'pendiente':
            fill_color = 'FFF4CC'  # Amarillo
        elif solicitud.estado == 'aprobada':
            fill_color = 'CCFFCC'  # Verde
        elif solicitud.estado == 'rechazada':
            fill_color = 'FFCCCC'  # Rojo
        else:
            fill_color = 'CCE5FF'  # Azul
        
        fila_datos = [
            solicitud.id,
            solicitud.fecha_solicitud.strftime('%d/%m/%Y %H:%M'),
            solicitud.solicitante.get_full_name() or solicitud.solicitante.username,
            solicitud.get_estado_display(),
            solicitud.total_items(),
            solicitud.total_cantidad(),
            solicitud.respondido_por.username if solicitud.respondido_por else '-',
            solicitud.fecha_respuesta.strftime('%d/%m/%Y %H:%M') if solicitud.fecha_respuesta else '-',
            solicitud.motivo[:50] + '...' if len(solicitud.motivo) > 50 else solicitud.motivo
        ]
        
        for col_num, valor in enumerate(fila_datos, 1):
            celda = ws.cell(row=row_num, column=col_num, value=valor)
            
            # Aplicar color
            if col_num == 4:  # Columna Estado
                celda.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
                celda.font = Font(bold=True)
            
            # Alineación
            if col_num in [1, 5, 6]:  # Columnas numéricas
                celda.alignment = Alignment(horizontal='center')
            else:
                celda.alignment = Alignment(horizontal='left')
    
    # Ajustar ancho de columnas
    anchos = [8, 18, 20, 15, 12, 15, 18, 18, 40]
    for col_num, ancho in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(col_num)].width = ancho
    
    # Preparar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=solicitudes_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


@login_required
def exportar_movimientos_excel(request):
    """
    Exportar movimientos a Excel (últimos 30 días)
    """
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Movimientos"
    
    # Headers
    headers = ['Fecha', 'Material', 'Código', 'Tipo', 'Cantidad', 
               'Usuario', 'Detalle']
    
    estilo_header = crear_estilo_header()
    
    # Escribir headers
    for col_num, header in enumerate(headers, 1):
        celda = ws.cell(row=1, column=col_num, value=header)
        aplicar_estilo_celda(celda, estilo_header)
    
    # Obtener datos (últimos 30 días)
    hace_30_dias = timezone.now() - timedelta(days=30)
    movimientos = Movimiento.objects.filter(
        fecha__gte=hace_30_dias
    ).select_related('material', 'usuario').order_by('-fecha')
    
    # Escribir datos
    for row_num, mov in enumerate(movimientos, 2):
        # Color según tipo
        if mov.tipo == 'entrada':
            fill_color = 'CCFFCC'  # Verde
        elif mov.tipo == 'salida':
            fill_color = 'FFCCCC'  # Rojo
        else:
            fill_color = 'FFF4CC'  # Amarillo
        
        fila_datos = [
            mov.fecha.strftime('%d/%m/%Y %H:%M'),
            mov.material.descripcion,
            mov.material.codigo,
            mov.tipo.upper(),
            mov.cantidad,
            f"{mov.usuario.nombre} {mov.usuario.apellido}",
            mov.detalle[:60] + '...' if mov.detalle and len(mov.detalle) > 60 else (mov.detalle or '-')
        ]
        
        for col_num, valor in enumerate(fila_datos, 1):
            celda = ws.cell(row=row_num, column=col_num, value=valor)
            
            # Aplicar color
            if col_num == 4:  # Columna Tipo
                celda.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
                celda.font = Font(bold=True)
            
            # Alineación
            if col_num == 5:  # Columna Cantidad
                celda.alignment = Alignment(horizontal='right')
            else:
                celda.alignment = Alignment(horizontal='left')
    
    # Ajustar ancho de columnas
    anchos = [18, 30, 15, 12, 12, 25, 45]
    for col_num, ancho in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(col_num)].width = ancho
    
    # Preparar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=movimientos_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response


@login_required
@user_passes_test(es_staff)
def exportar_reporte_completo_excel(request):
    """
    Reporte completo con múltiples hojas: Inventario, Solicitudes, Movimientos
    """
    # Crear workbook
    wb = Workbook()
    wb.remove(wb.active)  # Remover hoja por defecto
    
    estilo_header = crear_estilo_header()
    
    # ========== HOJA 1: RESUMEN ==========
    ws_resumen = wb.create_sheet("Resumen")
    
    # Título
    ws_resumen['A1'] = 'REPORTE COMPLETO - STOCKER'
    ws_resumen['A1'].font = Font(bold=True, size=16, color='366092')
    ws_resumen['A2'] = f'Generado: {timezone.now().strftime("%d/%m/%Y %H:%M")}'
    
    # KPIs
    ws_resumen['A4'] = 'INDICADORES CLAVE'
    ws_resumen['A4'].font = Font(bold=True, size=14)
    
    kpis = [
        ['Total Materiales', Material.objects.count()],
        ['Stock Total', Inventario.objects.aggregate(Sum('stock_actual'))['stock_actual__sum'] or 0],
        ['Materiales Críticos', Inventario.objects.filter(stock_actual__lte=F('stock_seguridad')).count()],
        ['Solicitudes Pendientes', Solicitud.objects.filter(estado='pendiente').count()],
        ['Solicitudes Mes Actual', Solicitud.objects.filter(fecha_solicitud__month=timezone.now().month).count()],
    ]
    
    for row_num, (label, valor) in enumerate(kpis, 5):
        ws_resumen[f'A{row_num}'] = label
        ws_resumen[f'B{row_num}'] = valor
        ws_resumen[f'A{row_num}'].font = Font(bold=True)
    
    # Ajustar ancho
    ws_resumen.column_dimensions['A'].width = 30
    ws_resumen.column_dimensions['B'].width = 20
    
    # ========== HOJA 2: INVENTARIO ==========
    ws_inv = wb.create_sheet("Inventario")
    headers_inv = ['Código', 'Descripción', 'Categoría', 'Stock Actual', 'Stock Seguridad', 'Estado']
    
    for col_num, header in enumerate(headers_inv, 1):
        celda = ws_inv.cell(row=1, column=col_num, value=header)
        aplicar_estilo_celda(celda, estilo_header)
    
    inventario = Inventario.objects.select_related('material').all()
    for row_num, inv in enumerate(inventario, 2):
        ws_inv.cell(row=row_num, column=1, value=inv.material.codigo)
        ws_inv.cell(row=row_num, column=2, value=inv.material.descripcion)
        ws_inv.cell(row=row_num, column=3, value=inv.material.get_categoria_display())
        ws_inv.cell(row=row_num, column=4, value=inv.stock_actual)
        ws_inv.cell(row=row_num, column=5, value=inv.stock_seguridad)
        
        estado = 'CRÍTICO' if inv.stock_actual <= inv.stock_seguridad else 'NORMAL'
        celda_estado = ws_inv.cell(row=row_num, column=6, value=estado)
        if estado == 'CRÍTICO':
            celda_estado.fill = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
    
    # Ajustar anchos
    for col in range(1, 7):
        ws_inv.column_dimensions[get_column_letter(col)].width = 20
    
    # ========== HOJA 3: SOLICITUDES RECIENTES ==========
    ws_sol = wb.create_sheet("Solicitudes")
    headers_sol = ['ID', 'Fecha', 'Solicitante', 'Estado', 'Items']
    
    for col_num, header in enumerate(headers_sol, 1):
        celda = ws_sol.cell(row=1, column=col_num, value=header)
        aplicar_estilo_celda(celda, estilo_header)
    
    solicitudes = Solicitud.objects.select_related('solicitante').prefetch_related('detalles').order_by('-fecha_solicitud')[:100]
    for row_num, sol in enumerate(solicitudes, 2):
        ws_sol.cell(row=row_num, column=1, value=sol.id)
        ws_sol.cell(row=row_num, column=2, value=sol.fecha_solicitud.strftime('%d/%m/%Y'))
        ws_sol.cell(row=row_num, column=3, value=sol.solicitante.username)
        ws_sol.cell(row=row_num, column=4, value=sol.get_estado_display())
        ws_sol.cell(row=row_num, column=5, value=sol.total_items())
    
    # Ajustar anchos
    for col in range(1, 6):
        ws_sol.column_dimensions[get_column_letter(col)].width = 18
    
    # Preparar respuesta
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=reporte_completo_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    wb.save(response)
    return response