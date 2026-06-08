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
    
    # Obtener usuario pipejarad
    try:
        usuario = get_user_model().objects.get(username='pipejarad')
        print(f'Usuario: {usuario.username} - {usuario.get_full_name()}')
        
        # Verificar si tiene portafolio
        if hasattr(usuario, 'portafolio'):
            print(f'Portafolio: {usuario.portafolio}')
        else:
            print('ERROR: Usuario no tiene portafolio!')
            sys.exit(1)
        
        # Obtener invitaciones pendientes
        invitaciones = Invitacion.objects.filter(musico=usuario, estado='pendiente')
        print(f'Invitaciones pendientes: {invitaciones.count()}')
        
        for inv in invitaciones:
            print(f'\nInvitación #{inv.id}: {inv.oferta_laboral.titulo}')
            print(f'  Estado: {inv.estado}')
            print(f'  Puede ser aceptada: {inv.puede_ser_aceptada()}')
            print(f'  Puede ser rechazada: {inv.puede_ser_rechazada()}')
            print(f'  Oferta vigente: {inv.oferta_laboral.esta_vigente()}')
            print(f'  Cupos restantes: {inv.oferta_laboral.get_cupos_restantes()}')
            print(f'  Ha expirado: {inv.ha_expirado()}')
            print(f'  Oferta estado: {inv.oferta_laboral.estado}')
            print(f'  Fecha expiración: {inv.fecha_expiracion}')
            
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
