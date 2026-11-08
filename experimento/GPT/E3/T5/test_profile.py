from contextlib import closing
from io import BytesIO
from pathlib import Path
import sqlite3
import tempfile
import unittest

from PIL import Image
from app import create_app


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.config = {
            "TESTING": True,
            "SECRET_KEY": "test-only-key",
            "DATABASE": str(Path(self.directory.name) / "test.sqlite3"),
            "UPLOAD_FOLDER": str(Path(self.directory.name) / "uploads"),
        }
        self.app = create_app(self.config)
        self.client = self.app.test_client()
        self.post("/cadastro", username="Maria", password="senha12345")
        self.post("/login", username="Maria", password="senha12345")

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, **fields):
        self.client.get("/login", follow_redirects=True)
        with self.client.session_transaction() as session:
            fields["csrf_token"] = session["csrf_token"]
        response = self.client.post(path, data=fields)
        response.request.close()
        response.request.environ["wsgi.input"].close()
        return response

    def image(self, format="PNG", color="red", size=(640, 320)):
        stream = BytesIO()
        Image.new("RGB", size, color).save(stream, format=format)
        stream.seek(0)
        return stream

    def filename(self, user_id=1):
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            return db.execute("SELECT profile_photo FROM users WHERE id = ?", (user_id,)).fetchone()[0]

    def files(self):
        return list(Path(self.config["UPLOAD_FOLDER"]).iterdir())

    def test_upload_display_and_normalization(self):
        response = self.post("/perfil", photo=(self.image(), "../../original.png"))
        self.assertEqual(response.status_code, 302)
        self.assertRegex(self.filename(), r"^[a-f0-9]{64}\.png$")
        self.assertEqual(len(self.files()), 1)
        photo = self.client.get("/usuarios/1/foto")
        self.assertEqual(photo.mimetype, "image/png")
        with Image.open(BytesIO(photo.data)) as image:
            self.assertEqual(image.size, (256, 128))
            self.assertEqual(image.mode, "RGB")
            self.assertNotIn("exif", image.info)
        for path in ("/", "/perfil", "/busca?q=Maria"):
            self.assertIn('src="/usuarios/1/foto"', self.client.get(path).text)

    def test_jpeg_and_webp(self):
        for format in ("JPEG", "WEBP"):
            response = self.post("/perfil", photo=(self.image(format), "foto." + format.lower()))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(self.client.get("/usuarios/1/foto").mimetype, "image/png")
        self.assertEqual(len(self.files()), 1)

    def test_replace_removes_previous_file(self):
        self.post("/perfil", photo=(self.image(), "primeira.png"))
        old = self.filename()
        old_data = self.client.get("/usuarios/1/foto").data
        self.post("/perfil", photo=(self.image(color="blue"), "segunda.png"))
        self.assertNotEqual(self.filename(), old)
        self.assertFalse((Path(self.config["UPLOAD_FOLDER"]) / old).exists())
        self.assertNotEqual(self.client.get("/usuarios/1/foto").data, old_data)
        self.assertEqual(len(self.files()), 1)

    def test_invalid_file_preserves_photo(self):
        self.post("/perfil", photo=(self.image(), "boa.png"))
        old = self.filename()
        for data in (b"<script>alert('x')</script>", b"<svg></svg>", b"broken image"):
            self.assertEqual(self.post("/perfil", photo=(BytesIO(data), "foto.png")).status_code, 400)
        self.assertEqual(self.filename(), old)
        self.assertEqual(len(self.files()), 1)

    def test_missing_empty_and_unsupported_file(self):
        self.assertEqual(self.post("/perfil").status_code, 400)
        self.assertEqual(self.post("/perfil", photo=(BytesIO(b""), "vazia.png")).status_code, 400)
        self.assertEqual(self.post("/perfil", photo=(self.image("GIF"), "foto.gif")).status_code, 400)
        self.assertIsNone(self.filename())
        self.assertEqual(self.files(), [])

    def test_upload_and_request_size_limits(self):
        data = b"x" * (5 * 1024 * 1024 + 1)
        self.assertEqual(self.post("/perfil", photo=(BytesIO(data), "grande.png")).status_code, 400)
        data = b"x" * (6 * 1024 * 1024 + 1)
        self.assertEqual(self.post("/perfil", photo=(BytesIO(data), "grande.png")).status_code, 413)
        self.assertEqual(self.files(), [])

    def test_dimension_limit(self):
        response = self.post("/perfil", photo=(self.image(size=(8193, 1)), "larga.png"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.files(), [])

    def test_guest_cannot_upload_or_read(self):
        self.post("/logout")
        for path in ("/perfil", "/usuarios/1/foto"):
            self.assertEqual(self.client.get(path).location, "/login")
        self.assertEqual(self.post("/perfil", photo=(self.image(), "foto.png")).location, "/login")
        self.assertEqual(self.files(), [])

    def test_csrf_required(self):
        for fields in ({}, {"csrf_token": "inválido"}):
            fields["photo"] = (self.image(), "foto.png")
            self.assertEqual(self.client.post("/perfil", data=fields).status_code, 400)
        self.assertEqual(self.files(), [])

    def test_author_comes_from_session(self):
        self.post("/logout")
        self.post("/cadastro", username="Pedro", password="senha12345")
        self.post("/login", username="Pedro", password="senha12345")
        self.post("/perfil", photo=(self.image(), "foto.png"), user_id="1")
        self.assertIsNone(self.filename(1))
        self.assertIsNotNone(self.filename(2))

    def test_photo_survives_restart(self):
        self.post("/perfil", photo=(self.image(), "foto.png"))
        expected = self.client.get("/usuarios/1/foto").data
        restarted = create_app(self.config).test_client()
        restarted.set_cookie("session", self.client.get_cookie("session").value)
        self.assertEqual(restarted.get("/usuarios/1/foto").data, expected)

    def test_missing_photo_and_unsafe_stored_path(self):
        self.assertEqual(self.client.get("/usuarios/1/foto").status_code, 404)
        self.assertEqual(self.client.get("/usuarios/999/foto").status_code, 404)
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.execute("UPDATE users SET profile_photo = '../outside.png' WHERE id = 1")
            db.commit()
        self.assertEqual(self.client.get("/usuarios/1/foto").status_code, 404)

    def test_database_failure_cleans_new_file(self):
        self.post("/perfil", photo=(self.image(), "boa.png"))
        old = self.filename()
        with closing(sqlite3.connect(self.config["DATABASE"])) as db:
            db.execute("""CREATE TRIGGER reject_photo BEFORE UPDATE OF profile_photo ON users
                          BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
            db.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.post("/perfil", photo=(self.image(color="blue"), "nova.png"))
        self.assertEqual(self.filename(), old)
        self.assertEqual(len(self.files()), 1)

    def test_existing_database_without_photo_column(self):
        legacy = str(Path(self.directory.name) / "legacy.sqlite3")
        with closing(sqlite3.connect(legacy)) as db:
            db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)")
            db.execute("INSERT INTO users VALUES (1, 'Existente', 'legacy-hash')")
            db.commit()
        config = {**self.config, "DATABASE": legacy}
        create_app(config)
        with closing(sqlite3.connect(legacy)) as db:
            self.assertEqual(db.execute("SELECT username, profile_photo FROM users").fetchone(), ("Existente", None))


if __name__ == "__main__":
    unittest.main()
