from pathlib import Path
import tempfile
import unittest

from app import create_app


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-key",
            "DATABASE": str(Path(self.directory.name) / "test.sqlite3"),
        })
        self.client = self.app.test_client()
        for name in ("Maria", "Pedro"):
            self.post("/cadastro", username=name, password="senha12345")
        self.post("/login", username="Maria", password="senha12345")
        self.post("/postagens/nova", content="Python e Flask: programação web.")
        self.post("/postagens/nova", content="Férias em São Paulo. 100% diversão.")
        self.post("/logout")
        self.post("/login", username="Pedro", password="senha12345")
        self.post("/postagens/nova", content="MARIA recomenda Python. Marcador_com_sublinhado")

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, **fields):
        self.client.get("/login", follow_redirects=True)
        with self.client.session_transaction() as session:
            fields["csrf_token"] = session["csrf_token"]
        return self.client.post(path, data=fields)

    def search(self, term):
        response = self.client.get("/busca", query_string={"q": term})
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_partial_user_match_case_insensitive(self):
        page = self.search("aRi")
        self.assertIn("Usuários encontrados (1)", page)
        self.assertIn("@Maria", page)
        self.assertIn("Postagens encontradas (1)", page)

    def test_posts_from_multiple_authors_and_sections(self):
        page = self.search("pYtHoN")
        self.assertIn("Usuários encontrados (0)", page)
        self.assertIn("Postagens encontradas (2)", page)
        self.assertIn("@Maria", page)
        self.assertIn("@Pedro", page)
        self.assertIn('href="/#post-1"', page)
        self.assertIn('href="/#post-3"', page)

    def test_unicode_and_trimmed_term(self):
        page = self.search("  FÉRIAS  ")
        self.assertIn("Postagens encontradas (1)", page)
        self.assertIn("Férias em São Paulo", page)
        self.assertIn("Postagens encontradas (1)", self.search("PROGRAMAÇÃO"))

    def test_literal_percent_and_underscore(self):
        self.assertIn("Postagens encontradas (1)", self.search("%"))
        self.assertIn("Postagens encontradas (1)", self.search("_"))

    def test_empty_invalid_and_no_results(self):
        for term in ("", "   "):
            self.assertIn("Informe um termo", self.search(term))
        for term in ("x" * 101, "\x00"):
            self.assertIn("Use um termo válido", self.search(term))
        page = self.search("inexistente987654")
        self.assertIn("Nenhum usuário encontrado", page)
        self.assertIn("Nenhuma postagem encontrada", page)

    def test_guest_is_redirected_and_field_is_available(self):
        self.assertIn('role="search"', self.client.get("/").text)
        self.post("/logout")
        response = self.client.get("/busca", query_string={"q": "Python"})
        self.assertEqual(response.location, "/login")
        self.assertNotIn("programação web", response.text)

    def test_sql_injection_and_html_escaping(self):
        page = self.search("' OR 1=1 --")
        self.assertIn("Postagens encontradas (0)", page)
        page = self.search("<script>alert('x')</script>")
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Postagens encontradas (2)", self.search("Python"))

    def test_search_reflects_create_edit_delete(self):
        self.post("/postagens/nova", content="TermoExclusivoNovo")
        self.assertIn("Postagens encontradas (1)", self.search("TermoExclusivoNovo"))
        self.post("/postagens/4/editar", content="TermoExclusivoEditado")
        self.assertIn("Postagens encontradas (0)", self.search("TermoExclusivoNovo"))
        self.assertIn("Postagens encontradas (1)", self.search("TermoExclusivoEditado"))
        self.post("/postagens/4/excluir")
        self.assertIn("Postagens encontradas (0)", self.search("TermoExclusivoEditado"))

    def test_comments_do_not_match_post_content_search(self):
        self.post("/postagens/1/comentarios", content="SEGREDO_COMENTARIO")
        self.assertIn("Postagens encontradas (0)", self.search("SEGREDO_COMENTARIO"))


if __name__ == "__main__":
    unittest.main()
