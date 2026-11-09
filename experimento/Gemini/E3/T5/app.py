import os
import uuid
import sqlite3
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g, abort, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'chave-secreta-para-desenvolvimento-troque-em-producao'
DATABASE = 'database.db'

# Configuração de upload de arquivos de imagem
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Limite máximo de 5MB por arquivo

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON;')
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        
        # Garante a migração caso a coluna 'avatar' não exista em versões anteriores
        cursor = db.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'avatar' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT 'default_avatar.svg'")
        db.commit()


def get_current_user():
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, avatar FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        if user is None:
            session.clear()
            return None
        return user
    return None


@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        SELECT p.id, p.content, p.created_at, p.updated_at, p.author_id,
               u.username AS author_name,
               COALESCE(u.avatar, 'default_avatar.svg') AS author_avatar
        FROM posts p
        JOIN users u ON p.author_id = u.id
        ORDER BY p.created_at DESC
    ''')
    posts_rows = cursor.fetchall()

    cursor.execute('''
        SELECT c.id, c.post_id, c.content, c.created_at, c.author_id,
               u.username AS author_name,
               COALESCE(u.avatar, 'default_avatar.svg') AS author_avatar
        FROM comments c
        JOIN users u ON c.author_id = u.id
        ORDER BY c.created_at ASC
    ''')
    comments_rows = cursor.fetchall()

    comments_by_post = {}
    for comment in comments_rows:
        pid = comment['post_id']
        if pid not in comments_by_post:
            comments_by_post[pid] = []
        comments_by_post[pid].append(comment)

    posts = []
    for post in posts_rows:
        posts.append({
            'id': post['id'],
            'content': post['content'],
            'created_at': post['created_at'],
            'updated_at': post['updated_at'],
            'author_id': post['author_id'],
            'author_name': post['author_name'],
            'author_avatar': post['author_avatar'],
            'comments': comments_by_post.get(post['id'], [])
        })

    return render_template('index.html', user=user, posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'warning')
            return render_template('register.html')

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Nome de usuário já cadastrado. Escolha outro.', 'danger')
            return render_template('register.html')

        hashed_password = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)',
            (username, hashed_password, 'default_avatar.svg')
        )
        db.commit()

        flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Informe o usuário e a senha.', 'warning')
            return render_template('login.html')

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username, password, avatar FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user['password'], password):
            flash('Usuário ou senha incorretos.', 'danger')
            return render_template('login.html')

        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['avatar'] = user['avatar'] or 'default_avatar.svg'
        flash(f'Bem-vindo(a), {user["username"]}!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Faça login para gerenciar seu perfil.', 'warning')
        return redirect(url_for('login'))

    user = get_current_user()
    if user is None:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'avatar' not in request.files:
            flash('Nenhum arquivo de imagem foi selecionado.', 'warning')
            return redirect(url_for('profile'))

        file = request.files['avatar']
        if file.filename == '':
            flash('Selecione uma imagem válida para enviar.', 'warning')
            return redirect(url_for('profile'))

        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"avatar_{session['user_id']}_{uuid.uuid4().hex[:8]}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

            # Salva o novo arquivo
            file.save(file_path)

            # Remove a imagem anterior caso não seja o avatar padrão
            old_avatar = user['avatar']
            if old_avatar and old_avatar != 'default_avatar.svg':
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_avatar)
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except OSError:
                        pass

            db = get_db()
            cursor = db.cursor()
            cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (unique_filename, session['user_id']))
            db.commit()

            session['avatar'] = unique_filename
            flash('Foto de perfil atualizada com sucesso!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Formato não suportado. Envie arquivos PNG, JPG, JPEG, GIF ou WEBP.', 'danger')
            return redirect(url_for('profile'))

    return render_template('profile.html', user=user)


@app.route('/posts/create', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        flash('Você precisa estar autenticado para publicar.', 'warning')
        return redirect(url_for('login'))

    content = request.form.get('content', '').strip()
    if not content:
        flash('O conteúdo da postagem não pode ser vazio.', 'warning')
        return redirect(url_for('index'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO posts (author_id, content) VALUES (?, ?)',
        (session['user_id'], content)
    )
    db.commit()
    flash('Postagem publicada com sucesso!', 'success')
    return redirect(url_for('index'))


@app.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        flash('Você precisa estar autenticado para editar publicações.', 'warning')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()

    if post is None:
        abort(404)

    if post['author_id'] != session['user_id']:
        flash('Você não tem permissão para editar esta postagem.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash('O conteúdo da postagem não pode ser vazio.', 'warning')
            return render_template('edit_post.html', post=post)

        cursor.execute(
            '''UPDATE posts 
               SET content = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?''',
            (content, post_id)
        )
        db.commit()
        flash('Postagem atualizada com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)


@app.route('/posts/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        flash('Você precisa estar autenticado para excluir publicações.', 'warning')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()

    if post is None:
        abort(404)

    if post['author_id'] != session['user_id']:
        flash('Você não tem permissão para excluir esta postagem.', 'danger')
        return redirect(url_for('index'))

    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    db.commit()
    flash('Postagem excluída com sucesso.', 'info')
    return redirect(url_for('index'))


@app.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        flash('Você precisa estar autenticado para comentar.', 'warning')
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT id FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()
    if post is None:
        abort(404)

    content = request.form.get('content', '').strip()
    if not content:
        flash('O comentário não pode ser vazio.', 'warning')
        return redirect(url_for('index'))

    cursor.execute(
        'INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)',
        (post_id, session['user_id'], content)
    )
    db.commit()
    flash('Comentário publicado!', 'success')
    return redirect(url_for('index'))


@app.route('/search')
def search():
    user = get_current_user()
    query = request.args.get('q', '').strip()
    matched_users = []
    matched_posts = []

    if query:
        db = get_db()
        cursor = db.cursor()
        search_term = f"%{query}%"

        cursor.execute('''
            SELECT id, username, avatar, created_at
            FROM users
            WHERE username LIKE ?
            ORDER BY username ASC
        ''', (search_term,))
        matched_users = cursor.fetchall()

        cursor.execute('''
            SELECT p.id, p.content, p.created_at, p.updated_at, p.author_id,
                   u.username AS author_name,
                   COALESCE(u.avatar, 'default_avatar.svg') AS author_avatar
            FROM posts p
            JOIN users u ON p.author_id = u.id
            WHERE p.content LIKE ?
            ORDER BY p.created_at DESC
        ''', (search_term,))
        posts_rows = cursor.fetchall()

        if posts_rows:
            post_ids = [p['id'] for p in posts_rows]
            placeholders = ','.join(['?'] * len(post_ids))
            cursor.execute(f'''
                SELECT c.id, c.post_id, c.content, c.created_at, c.author_id,
                       u.username AS author_name,
                       COALESCE(u.avatar, 'default_avatar.svg') AS author_avatar
                FROM comments c
                JOIN users u ON c.author_id = u.id
                WHERE c.post_id IN ({placeholders})
                ORDER BY c.created_at ASC
            ''', post_ids)
            comments_rows = cursor.fetchall()

            comments_by_post = {}
            for comment in comments_rows:
                pid = comment['post_id']
                if pid not in comments_by_post:
                    comments_by_post[pid] = []
                comments_by_post[pid].append(comment)

            for post in posts_rows:
                matched_posts.append({
                    'id': post['id'],
                    'content': post['content'],
                    'created_at': post['created_at'],
                    'updated_at': post['updated_at'],
                    'author_id': post['author_id'],
                    'author_name': post['author_name'],
                    'author_avatar': post['author_avatar'],
                    'comments': comments_by_post.get(post['id'], [])
                })

    return render_template(
        'search.html',
        user=user,
        query=query,
        matched_users=matched_users,
        matched_posts=matched_posts
    )


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
