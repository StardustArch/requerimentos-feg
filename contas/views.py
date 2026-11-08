from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CompletarPerfilForm
from .models import Perfil


@login_required
def dashboard_redirect(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    return render(request, "contas/home.html", {"perfil": perfil})


@login_required
def completar_perfil(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = CompletarPerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil académico actualizado.")
            return redirect("home")
    else:
        form = CompletarPerfilForm(instance=perfil)

    return render(
        request,
        "contas/completar_perfil.html",
        {"form": form, "perfil": perfil},
    )
