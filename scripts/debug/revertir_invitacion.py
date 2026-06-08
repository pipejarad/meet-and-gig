#!/usr/bin/env python
import os
import sys
import django

# Setup Django
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meetandgig.settings')
    django.setup()
    
    from usuarios.models import *
    from django.contrib.auth import get_user_model
    
    # Revertir la invitación a pendiente para pruebas
    try:
        invitacion = Invitacion.objects.get(id=2)
        postulacion = invitacion.postulacion_creada
        
        # Eliminar la postulación si existe
        if postulacion:
            print(f"Eliminando postulación: {postulacion}")
            postulacion.delete()
        
        # Revertir invitación a pendiente
        invitacion.estado = 'pendiente'
        invitacion.postulacion_creada = None
        invitacion.mensaje_respuesta = ''
        invitacion.fecha_respuesta = None
        invitacion.save()
        
        print(f"Invitación #{invitacion.id} revertida a estado pendiente")
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
