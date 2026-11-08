from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from app import create_app


class CommentTests(unittest.TestCase):
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
        self.post("/postagens/nova", content="Primeira postagem")
        self.post("/postagens/nova", content="Segunda postagem")

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, **fields):
        self.client.get("/login", follow_redirects=True)
        with self.client.session_transaction() as session:
            fields["csrf_token"] = session["csrf_token"]
        return self.client.post(path, data=fields)

    def comments(self):
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.row_factory = sqlite3.Row
            return db.execute("SELECT * FROM comments ORDER BY id").fetchall()

    def test_comment_links_author_post_and_survives_restart(self):
        response = self.post("/postagens/1/comentarios", content="Olá, pessoal!")
        self.assertEqual(response.location, "/#post-1")
        row = self.comments()[0]
        self.assertEqual((row["post_id"], row["author_id"], row["content"]), (1, 1, "Olá, pessoal!"))
        self.assertTrue(row["created_at"])
        restarted = create_app(self.config).test_client()
        restarted.set_cookie("session", self.client.get_cookie("session").value)
        page = restarted.get("/").text
        self.assertIn("Olá, pessoal!", page)
        self.assertIn("@Maria", page)

    def test_other_user_can_comment_and_cannot_forge_links(self):
        self.post("/logout")
        self.post("/login", username="Pedro", password="senha12345")
        self.post("/postagens/1/comentarios", content="Comentário do Pedro", author_id="1", post_id="2")
        row = self.comments()[0]
        self.assertEqual((row["post_id"], row["author_id"]), (1, 2))
        page = self.client.get("/").text
        self.assertIn("Comentário do Pedro", page)
        self.assertIn("@Pedro", page)

    def test_comments_display_under_correct_post(self):
        self.post("/postagens/1/comentarios", content="EXCLUSIVO_PRIMEIRA")
        self.post("/postagens/2/comentarios", content="EXCLUSIVO_SEGUNDA")
        page = self.client.get("/").text
        second = page.split('id="post-2"', 1)[1].split('id="post-1"', 1)[0]
        first = page.split('id="post-1"', 1)[1]
        self.assertIn("EXCLUSIVO_SEGUNDA", second)
        self.assertNotIn("EXCLUSIVO_PRIMEIRA", second)
        self.assertIn("EXCLUSIVO_PRIMEIRA", first)
        self.assertNotIn("EXCLUSIVO_SEGUNDA", first)

    def test_guest_and_missing_csrf_are_rejected(self):
        self.assertEqual(self.client.post("/postagens/1/comentarios", data={"content": "Ataque"}).status_code, 400)
        self.post("/logout")
        response = self.post("/postagens/1/comentarios", content="Indevido")
        self.assertEqual(response.location, "/login")
        self.assertEqual(self.comments(), [])

    def test_validation_and_unicode_boundary(self):
        for content in ("", " \n\t ", "x" * 2001, "\x00"):
            self.post("/postagens/1/comentarios", content=content)
        self.assertEqual(self.comments(), [])
        self.post("/postagens/1/comentarios", content="😀" * 2000)
        self.assertEqual(len(self.comments()[0]["content"]), 2000)

    def test_missing_post_and_get_method(self):
        self.assertEqual(self.post("/postagens/999/comentarios", content="Nada").status_code, 404)
        self.assertEqual(self.client.get("/postagens/1/comentarios").status_code, 405)
        self.assertEqual(self.comments(), [])

    def test_xss_sql_text_and_line_breaks(self):
        content = "<script>alert('x')</script>\n'; DROP TABLE posts; --"
        self.post("/postagens/1/comentarios", content=content)
        self.assertEqual(self.comments()[0]["content"], content)
        page = self.client.get("/").text
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("Primeira postagem", page)

    def test_post_edit_preserves_and_delete_cascades_comments(self):
        self.post("/postagens/1/comentarios", content="Comentário da primeira")
        self.post("/postagens/2/comentarios", content="Comentário da segunda")
        self.post("/postagens/1/editar", content="Postagem alterada")
        self.assertEqual(len(self.comments()), 2)
        self.post("/postagens/1/excluir")
        rows = self.comments()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["post_id"], 2)
        self.assertNotIn("Comentário da primeira", self.client.get("/").text)

    def test_existing_t2_database(self):
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.execute("DROP TABLE comments")
            db.commit()
        upgraded = create_app(self.config).test_client()
        upgraded.set_cookie("session", self.client.get_cookie("session").value)
        page = upgraded.get("/").text
        self.assertIn("Primeira postagem", page)
        self.assertIn("Você está autenticado", page)
        self.assertEqual(self.comments(), [])


if __name__ == "__main__":
    unittest.main()
