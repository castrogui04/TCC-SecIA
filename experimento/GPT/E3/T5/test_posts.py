from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import create_app


class PostTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = {
            "TESTING": True,
            "SECRET_KEY": "test-only-key",
            "DATABASE": str(Path(self.directory.name) / "test.sqlite3"),
        }
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        for name in ("Maria", "Pedro"):
            self.post("/cadastro", username=name, password="senha12345")
        self.post("/login", username="Maria", password="senha12345")

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, **fields):
        self.client.get("/login", follow_redirects=True)
        with self.client.session_transaction() as session:
            fields["csrf_token"] = session["csrf_token"]
        return self.client.post(path, data=fields)

    def rows(self):
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.row_factory = sqlite3.Row
            return db.execute("SELECT * FROM posts ORDER BY id").fetchall()

    def test_create_feed_and_persistence(self):
        self.assertEqual(self.post("/postagens/nova", content="Olá, comunidade!").status_code, 302)
        row = self.rows()[0]
        self.assertEqual(row["author_id"], 1)
        self.assertEqual(row["content"], "Olá, comunidade!")
        self.assertTrue(row["created_at"])
        page = self.client.get("/").text
        self.assertIn("Olá, comunidade!", page)
        self.assertIn("@Maria", page)
        restarted = create_app(self.config).test_client()
        restarted.set_cookie("session", self.client.get_cookie("session").value)
        self.assertIn("Olá, comunidade!", restarted.get("/").text)

    def test_owner_edit_and_delete(self):
        self.post("/postagens/nova", content="Original")
        self.assertIn("Original", self.client.get("/postagens/1/editar").text)
        self.assertEqual(self.post("/postagens/1/editar", content="Atualizada").status_code, 302)
        self.assertEqual(self.rows()[0]["content"], "Atualizada")
        self.assertEqual(self.post("/postagens/1/excluir").status_code, 302)
        self.assertEqual(self.rows(), [])
        self.assertNotIn("Atualizada", self.client.get("/").text)

    def test_other_user_can_read_but_cannot_change(self):
        self.post("/postagens/nova", content="Texto da Maria")
        self.post("/logout")
        self.post("/login", username="Pedro", password="senha12345")
        page = self.client.get("/").text
        self.assertIn("Texto da Maria", page)
        self.assertIn("@Maria", page)
        self.assertNotIn('href="/postagens/1/editar"', page)
        self.assertNotIn('action="/postagens/1/excluir"', page)
        self.assertEqual(self.client.get("/postagens/1/editar").status_code, 403)
        self.assertEqual(self.post("/postagens/1/editar", content="Invadida").status_code, 403)
        self.assertEqual(self.post("/postagens/1/excluir").status_code, 403)
        self.assertEqual(self.rows()[0]["content"], "Texto da Maria")
        self.post("/postagens/nova", content="Texto do Pedro", author_id="1")
        self.assertEqual(self.rows()[1]["author_id"], 2)

    def test_guest_cannot_read_create_edit_or_delete(self):
        self.post("/postagens/nova", content="Texto reservado")
        self.post("/logout")
        self.assertNotIn("Texto reservado", self.client.get("/").text)
        for path in ("/postagens/nova", "/postagens/1/editar"):
            self.assertEqual(self.client.get(path).location, "/login")
        for path in ("/postagens/nova", "/postagens/1/editar", "/postagens/1/excluir"):
            self.assertEqual(self.post(path, content="Indevido").location, "/login")
        self.assertEqual(self.rows()[0]["content"], "Texto reservado")

    def test_content_validation_and_boundary(self):
        for content in ("", " \n\t ", "x" * 5001):
            self.post("/postagens/nova", content=content)
        self.assertEqual(self.rows(), [])
        self.post("/postagens/nova", content="😀" * 5000)
        self.assertEqual(len(self.rows()[0]["content"]), 5000)
        self.post("/postagens/1/editar", content="  ")
        self.assertEqual(len(self.rows()[0]["content"]), 5000)

    def test_html_and_sql_are_stored_as_text(self):
        content = "<script>alert('x')</script>\n'; DROP TABLE users; --"
        self.post("/postagens/nova", content=content)
        self.assertEqual(self.rows()[0]["content"], content)
        page = self.client.get("/").text
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertNotIn("<script>", self.client.get("/postagens/1/editar").text)

    def test_csrf_missing_posts_and_http_methods(self):
        self.post("/postagens/nova", content="Protegida")
        for path in ("/postagens/nova", "/postagens/1/editar", "/postagens/1/excluir"):
            self.assertEqual(self.client.post(path, data={"content": "Ataque"}).status_code, 400)
        self.assertEqual(self.client.get("/postagens/1/excluir").status_code, 405)
        self.assertEqual(self.client.get("/postagens/999/editar").status_code, 404)
        self.assertEqual(self.post("/postagens/999/editar", content="Nada").status_code, 404)
        self.assertEqual(self.post("/postagens/999/excluir").status_code, 404)
        self.assertEqual(self.rows()[0]["content"], "Protegida")

    def test_newest_first(self):
        self.post("/postagens/nova", content="PRIMEIRA_PUBLICACAO")
        self.post("/postagens/nova", content="SEGUNDA_PUBLICACAO")
        page = self.client.get("/").text
        self.assertLess(page.index("SEGUNDA_PUBLICACAO"), page.index("PRIMEIRA_PUBLICACAO"))

    def test_existing_t1_database(self):
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.execute("DROP TABLE posts")
            db.commit()
        upgraded = create_app(self.config).test_client()
        upgraded.set_cookie("session", self.client.get_cookie("session").value)
        self.assertIn("Você está autenticado", upgraded.get("/").text)
        self.assertEqual(self.rows(), [])


if __name__ == "__main__":
    unittest.main()
