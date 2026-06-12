from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


def identificador_para_axes(request, credentials=None):
    """Identificador con el que django-axes cuenta intentos fallidos (A4).

    No basta el default de axes: busca la credencial bajo el USERNAME_FIELD
    del modelo ('email'), pero el form de login la envía bajo 'username'
    (que aquí puede ser email O username), así que axes registraba None y
    el bloqueo por usuario+IP nunca coincidía. Se cubren ambas claves y se
    normaliza a minúsculas para que 'Pedro@X.com' y 'pedro@x.com' cuenten
    contra el mismo objetivo.
    """
    fuentes = [credentials or {}]
    if request is not None:
        fuentes.append(getattr(request, 'POST', None) or {})
    for fuente in fuentes:
        for clave in ('username', 'email'):
            valor = fuente.get(clave)
            if valor:
                return str(valor).strip().lower()
    return None


class EmailBackend(ModelBackend):
    """
    Backend de autenticación personalizado que permite login con email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        # Buscar PRIMERO por email (USERNAME_FIELD, único) y solo si no hay
        # match, por username. Un get() con Q(email)|Q(username) puede devolver
        # dos filas cuando el username de un usuario coincide con el email de
        # otro (el validador por defecto permite '@' en usernames), y el
        # MultipleObjectsReturned resultante bloqueaba el login (hallazgo A3).
        user = User.objects.filter(email__iexact=username).order_by('pk').first()
        if user is None:
            user = User.objects.filter(username__iexact=username).order_by('pk').first()

        if user is None:
            # Ejecutar hasher para prevenir timing attacks
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
