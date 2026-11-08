from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import Perfil


def papel_utilizador(user):
    """Devolve o papel do utilizador, ou None se não tiver perfil."""
    if not user or not user.is_authenticated:
        return None

    perfil = getattr(user, "perfil", None)
    return perfil.papel if perfil is not None else None


def e_admin(user):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or papel_utilizador(user) == Perfil.PAPEL_ADMIN)
    )


def _permitir(user, papeis):
    if e_admin(user):
        return True
    return papel_utilizador(user) in papeis


def _decorador(papeis):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not _permitir(request.user, papeis):
                raise PermissionDenied(
                    "Não tem permissão para aceder a esta página."
                )
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


estudante_required = _decorador({Perfil.PAPEL_ESTUDANTE})
secretaria_required = _decorador({Perfil.PAPEL_SECRETARIA})
credito_required = _decorador({Perfil.PAPEL_CREDITO})
registo_required = _decorador({Perfil.PAPEL_REGISTO})

PAPEIS_STAFF = {
    Perfil.PAPEL_SECRETARIA,
    Perfil.PAPEL_CREDITO,
    Perfil.PAPEL_REGISTO,
    Perfil.PAPEL_ADMIN,
}
staff_required = _decorador(PAPEIS_STAFF)
admin_required = _decorador({Perfil.PAPEL_ADMIN})
