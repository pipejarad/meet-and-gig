# Scripts de Desarrollo y Utilidades

Este directorio contiene scripts de utilidad para desarrollo, debugging y mantenimiento del proyecto.

## 📁 Estructura

### `/desarrollo/`

Scripts para facilitar el desarrollo y visualización de datos:

- **`mostrar_resumen_perfiles.py`**: Muestra un resumen de perfiles de músicos creados en la BD

  - Uso: `python scripts/desarrollo/mostrar_resumen_perfiles.py`
  - Útil para verificar datos de desarrollo

- **`verificar_perfiles.py`**: Verifica y limpia perfiles de demostración específicos
  - Uso: `python scripts/desarrollo/verificar_perfiles.py`
  - Verifica 6 perfiles de músicos de demostración
  - Permite limpiar usuarios incompletos

### `/data/`

Scripts para manejo y creación de datos:

- **`crear_perfiles_musicos.py`**: Crea perfiles de músicos con datos de prueba
  - Uso: `python scripts/data/crear_perfiles_musicos.py`
  - Útil para poblar la BD en desarrollo

## 🧪 Scripts de Testing

- **`test_commands.ps1`**: Funciones de PowerShell para automatizar testing
  - Uso: `. .\scripts\test_commands.ps1` (cargar funciones)
  - Funciones disponibles: `Test-All`, `Test-Unit`, `Test-Coverage`, etc.
  - Incluye limpieza de cache y instalación de dependencias

## 💡 Uso

Todos los scripts están configurados para:

- Ejecutarse desde la raíz del proyecto
- Configurar Django automáticamente
- Funcionar con la BD actual

### Ejemplos de Uso:

```bash
# Scripts Python
python scripts/desarrollo/verificar_perfiles.py
python scripts/data/crear_perfiles_musicos.py

# Scripts PowerShell
. .\scripts\test_commands.ps1
Test-All
Test-Unit
Clean-TestCache
```

## ⚠️ Importante

Estos scripts son para **desarrollo únicamente**. No usar en producción.
