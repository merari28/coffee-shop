from django.core.mail import send_mail
from django.conf import settings
from django.views import generic
from django.urls import reverse_lazy

from .forms import SignupForm


class RegisterView(generic.CreateView):
    form_class = SignupForm
    template_name = "users/register.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        # Send a welcome email (console backend by default — no SMTP required).
        send_mail(
            subject="☕ ¡Bienvenido a Coffee Shop!",
            message=(
                f"Hola {user.username},\n\n"
                "Gracias por registrarte en Coffee Shop. Tu cuenta ya está activa: "
                "inicia sesión y arma tu primer pedido.\n\n"
                "Nos vemos en la barra,\n"
                "El equipo de Coffee Shop"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email] if user.email else [],
            fail_silently=True,
        )
        return response
