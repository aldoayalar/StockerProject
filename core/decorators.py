from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

#Decoradores personalizados para control de acceso por roles.

def verificar_rol(rol_requerido):
    """
    Decorador para verificar el rol del usuario.
    Acepta un solo rol (str) o una lista de roles (list).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar si es lista de roles o un solo rol
            if isinstance(rol_requerido, list):
                if request.user.rol not in rol_requerido:
                    messages.error(request, 'No tienes permisos para acceder a esta sección.')
                    return redirect('dashboard')
            else:
                if request.user.rol != rol_requerido:
                    messages.error(request, 'No tienes permisos para acceder a esta sección.')
                    return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
