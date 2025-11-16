from django.shortcuts import render

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
