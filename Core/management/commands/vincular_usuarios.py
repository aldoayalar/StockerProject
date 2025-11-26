# core/management/commands/vincular_usuarios.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Usuario, Rol
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Vincula usuarios de Django con la tabla Usuario'

    def handle(self, *args, **kwargs):
        # Obtener o crear rol por defecto
        rol_default, _ = Rol.objects.get_or_create(nombre='tecnico')
        
        usuarios_creados = 0
        usuarios_existentes = 0
        
        for user in User.objects.all():
            # Verificar si ya existe
            if Usuario.objects.filter(email=user.email).exists():
                usuarios_existentes += 1
                self.stdout.write(f'Usuario ya existe: {user.email}')
            else:
                # Crear usuario personalizado
                Usuario.objects.create(
                    nombre=user.first_name or user.username,
                    apellido=user.last_name or '',
                    email=user.email or f'{user.username}@stocker.local',
                    password_hash=user.password,
                    activo=user.is_active,
                    rol=rol_default
                )
                usuarios_creados += 1
                self.stdout.write(self.style.SUCCESS(f'Usuario creado: {user.username}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nResumen:\n'
            f'- Usuarios creados: {usuarios_creados}\n'
            f'- Usuarios existentes: {usuarios_existentes}'
        ))
