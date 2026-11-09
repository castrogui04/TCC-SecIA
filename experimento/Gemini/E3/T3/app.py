import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave-secreta-para-desenvolvimento-troque-em-producao'
DATABASE = 'database.db'


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
        db.commit()


def get_current_user():
    if 'user_id' in session:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, username FROM users WHERE id = ?', (session['user_id'],))
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

    # Busca todas as postagens com o nome do respectivo autor
    cursor.execute('''
        SELECT p.id, p.content, p.created_at, p.updated_at, p.author_id, u.username AS author_name
        FROM posts p
        JOIN users u ON p.author_id = u.id
        ORDER BY p.created_at DESC
    ''')
    posts_rows = cursor.fetchall()

    # Busca todos os comentários ordenados cronologicamente
    cursor.execute('''
        SELECT c.id, c.post_id, c.content, c.created_at, c.author_id, u.username AS author_name
        FROM comments c
        JOIN users u ON c.author_id = u.id
        ORDER BY c.created_at ASC
    ''')
    comments_rows = cursor.fetchall()

    # Agrupa os comentários por ID da postagem
    comments_by_post = {}
    for comment in comments_rows:
        post_id = comment['post_id']
        if post_id not in comments_by_post:
            comments_by_post[post_id] = []
        comments_by_post[post_id].append(comment)

    # Constrói a lista estruturada de posts com seus comentários acoplados
    posts = []
    for post in posts_rows:
        posts.append({
            'id': post['id'],
            'content': post['content'],
            'created_at': post['created_at'],
            'updated_at': post['updated_at'],
            'author_id': post['author_id'],
            'author_name': post['author_name'],
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
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
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
        cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user['password'], password):
            flash('Usuário ou senha incorretos.', 'danger')
            return render_template('login.html')

        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash(f'Bem-vindo(a), {user["username"]}!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))


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

    # Valida se o post existe antes de adicionar o comentário
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


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
