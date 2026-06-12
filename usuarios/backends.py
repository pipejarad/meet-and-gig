from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


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
