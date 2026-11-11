"""Testes da página de styleguide (/dev/styleguide/)."""

from django.test import TestCase, override_settings
from django.urls import reverse


class StyleguideTests(TestCase):
    @override_settings(DEBUG=True)
    def test_styleguide_aceso_com_debug(self):
        """Com DEBUG=True devolve 200 e renderiza os componentes."""
        resposta = self.client.get(reverse("styleguide"), HTTP_HOST="127.0.0.1")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Styleguide de componentes")
        self.assertContains(resposta, "btn-primary")
        self.assertContains(resposta, "status-pill")
        self.assertContains(resposta, 'role="progressbar"')
        self.assertContains(resposta, "Styleguide de componentes")
        self.assertContains(resposta, "btn-primary")
        self.assertContains(resposta, "status-pill")
        self.assertContains(resposta, 'role="progressbar"')

    @override_settings(DEBUG=False)
    def test_styleguide_sem_debug_devolve_404(self):
        """Com DEBUG=False devolve 404."""
        resposta = self.client.get(reverse("styleguide"), HTTP_HOST="127.0.0.1")
        self.assertEqual(resposta.status_code, 404)
