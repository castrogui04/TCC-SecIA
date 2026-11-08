from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from werkzeug.security import check_password_hash

from app import create_app


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = {
            "TESTING": True,
            "SECRET_KEY": "test-only-key",
            "DATABASE": str(Path(self.directory.name) / "test.sqlite3"),
        }
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def post_form(self, path, **fields):
        self.client.get("/" if path == "/logout" else path)
        with self.client.session_transaction() as session:
            fields["csrf_token"] = session["csrf_token"]
        return self.client.post(path, data=fields, follow_redirects=True)

    def register(self):
        return self.post_form("/cadastro", username="Maria", password="senha12345")

    def login(self):
        return self.post_form("/login", username="maria", password="senha12345")

    def test_registration_hash_and_duplicate(self):
        self.assertIn("Cadastro realizado", self.register().text)
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            password_hash = db.execute("SELECT password_hash FROM users").fetchone()[0]
        self.assertNotEqual(password_hash, "senha12345")
        self.assertTrue(check_password_hash(password_hash, "senha12345"))
        response = self.post_form("/cadastro", username="MARIA", password="outrasenha")
        self.assertIn("já está cadastrado", response.text)

    def test_login_persistence_restart_and_logout(self):
        self.register()
        self.assertIn("Você está autenticado", self.login().text)
        self.assertIn("Maria", self.client.get("/").text)
        cookie = self.client.get_cookie("session")
        self.assertIsNotNone(cookie.expires)
        self.assertTrue(cookie.http_only)
        restarted = create_app(self.config).test_client()
        restarted.set_cookie("session", cookie.value)
        self.assertIn("Você está autenticado", restarted.get("/").text)
        self.assertIn("Nenhum usuário", self.post_form("/logout").text)
        self.assertIn("Nenhum usuário", self.client.get("/").text)

    def test_invalid_login_and_sql_injection(self):
        self.register()
        for username, password in [("Maria", "errada"), ("inexistente", "senha12345"),
                                   ("' OR 1=1 --", "senha12345")]:
            response = self.post_form("/login", username=username, password=password)
            self.assertIn("Usuário ou senha inválidos", response.text)
            self.assertIn("Nenhum usuário", self.client.get("/").text)

    def test_invalid_registration(self):
        for username, password in [("", ""), ("ab", "senha12345"),
                                   ("a" * 31, "senha12345"), ("<script>", "senha12345"),
                                   ("Maria", "curta"), ("Maria", " " * 8),
                                   ("Maria", "s" * 129)]:
            self.post_form("/cadastro", username=username, password=password)
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 0)

    def test_csrf_and_logout_method(self):
        for path in ("/cadastro", "/login", "/logout"):
            self.assertEqual(self.client.post(path).status_code, 400)
            self.assertEqual(self.client.post(path, data={"csrf_token": "inválido"}).status_code, 400)
        self.assertEqual(self.client.get("/logout").status_code, 405)

    def test_form_escaping(self):
        response = self.post_form("/cadastro", username='<script>alert("x")</script>', password="senha12345")
        self.assertNotIn('<script>alert("x")</script>', response.text)
        self.assertIn("&lt;script&gt;", response.text)

    def test_deleted_user_and_signed_cookie(self):
        self.register()
        self.login()
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.execute("DELETE FROM users")
            db.commit()
        self.assertIn("Nenhum usuário", self.client.get("/").text)
        self.client.set_cookie("session", "cookie-adulterado")
        self.assertIn("Nenhum usuário", self.client.get("/").text)


if __name__ == "__main__":
    unittest.main()
