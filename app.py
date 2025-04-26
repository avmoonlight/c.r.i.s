from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import pymysql

app = Flask(__name__)
app.secret_key = 'segredo'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Garante que a pasta de upload exista
os.makedirs(os.path.join(app.root_path, 'static', app.config['UPLOAD_FOLDER']), exist_ok=True)

# Função para conexão com o banco de dados
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='agentes_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# Função para salvar imagem e retornar caminho relativo
def salvar_imagem(imagem):
    if imagem and imagem.filename:
        filename = secure_filename(imagem.filename)
        caminho_relativo = os.path.join(app.config['UPLOAD_FOLDER'], filename).replace('\\', '/')
        caminho_completo = os.path.join(app.root_path, 'static', caminho_relativo)
        imagem.save(caminho_completo)
        return caminho_relativo
    return ''

# Rota de login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        senha = request.form['senha']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE id = %s AND senha = %s', (user_id, senha))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['usuario'] = user['username']
            session['usuario_id'] = user['id']
            session['is_admin'] = (user['username'] == 'adm')
            
            if user['id'] != 1:
                return redirect(url_for('agentes'))
            return redirect(url_for('dashboard'))
        else:
            flash('Login inválido')
            return redirect(url_for('login'))
    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', admin=session.get('is_admin'))

# Listar usuários
@app.route('/usuarios')
def usuarios():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios')
    users = cursor.fetchall()
    conn.close()

    return render_template('usuarios.html', usuarios=users)

# Criar usuário
@app.route('/usuarios/criar', methods=['GET', 'POST'])
def criar_usuario():
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        imagem = request.files.get('imagem')
        imagem_path = salvar_imagem(imagem)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO usuarios (username, senha, imagem) VALUES (%s, %s, %s)',
            (username, senha, imagem_path)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('usuarios'))

    return render_template('criar_usuario.html')

# Deletar usuário
@app.route('/usuarios/deletar/<int:id>')
def deletar_usuario(id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = %s', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('usuarios'))


# Editar usuário
@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if not session.get('is_admin'):
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        imagem = request.files.get('imagem')

        if imagem and imagem.filename:
            imagem_path = salvar_imagem(imagem)
        else:
            cursor.execute("SELECT imagem FROM usuarios WHERE id = %s", (id,))
            user = cursor.fetchone()
            imagem_path = user['imagem']

        cursor.execute(
            "UPDATE usuarios SET username = %s, senha = %s, imagem = %s WHERE id = %s",
            (username, senha, imagem_path, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('usuarios'))

    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('editar_usuario.html', usuario=user)


# Listar e criar agentes
@app.route('/agentes', methods=['GET', 'POST'])
def agentes():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        sobrenome = request.form.get('sobrenome')
        data_nasc = request.form.get('data_nasc')
        contato = request.form.get('contato_emergencia')
        observacoes = request.form.get('observacoes')
        status = 'vivo' if request.form.get('status') else 'morto'

        imagem = request.files.get('imagem')
        caminho_relativo = salvar_imagem(imagem)

        cursor.execute("""
            INSERT INTO agentes (nome, sobrenome, data_nasc, contato_emergencia, observacoes, imagem, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (nome, sobrenome, data_nasc, contato, observacoes, caminho_relativo, status))
        conn.commit()

    cursor.execute("SELECT * FROM agentes")
    agentes = cursor.fetchall()
    conn.close()
    return render_template('agentes.html', agentes=agentes)

# Editar agente
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        sobrenome = request.form.get('sobrenome')
        data_nasc = request.form.get('data_nasc')
        contato = request.form.get('contato_emergencia')
        observacoes = request.form.get('observacoes')
        status = 'vivo' if request.form.get('status') else 'morto'

        imagem = request.files.get('imagem')
        if imagem and imagem.filename:
            caminho_relativo = salvar_imagem(imagem)
        else:
            cursor.execute("SELECT imagem FROM agentes WHERE id = %s", (id,))
            agente = cursor.fetchone()
            caminho_relativo = agente['imagem']

        cursor.execute("""
            UPDATE agentes
            SET nome = %s, sobrenome = %s, data_nasc = %s, contato_emergencia = %s, observacoes = %s, imagem = %s, status = %s
            WHERE id = %s
        """, (nome, sobrenome, data_nasc, contato, observacoes, caminho_relativo, status, id))
        conn.commit()
        conn.close()
        return redirect(url_for('agentes'))

    cursor.execute("SELECT * FROM agentes WHERE id = %s", (id,))
    agente = cursor.fetchone()
    conn.close()
    return render_template('editar.html', agente=agente)

# Deletar agente (confirmação via GET e exclusão via POST)
@app.route('/deletar/<int:id>', methods=['GET', 'POST'])
def deletar(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT * FROM agentes WHERE id = %s", (id,))
        agente = cursor.fetchone()
        conn.close()
        return render_template('confirmar_deletar.html', agente=agente)

    elif request.method == 'POST':
        cursor.execute("DELETE FROM agentes WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('agentes'))
    
# Rotas para Criaturas (Bestiário)
@app.route('/criaturas', methods=['GET', 'POST'])
def criaturas():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        elemento = request.form.get('elemento')
        raridade = request.form.get('raridade')
        imagem = request.files.get('imagem')
        imagem_path = salvar_imagem(imagem)

        cursor.execute("""
            INSERT INTO criaturas (nome, elemento, imagem, raridade)
            VALUES (%s, %s, %s, %s)
        """, (nome, elemento, imagem_path, raridade))
        conn.commit()

    cursor.execute("SELECT * FROM criaturas")
    lista_criaturas = cursor.fetchall()
    conn.close()
    return render_template('criaturas.html', criaturas=lista_criaturas)

@app.route('/criaturas/editar/<int:id>', methods=['GET', 'POST'])
def editar_criatura(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        elemento = request.form.get('elemento')
        raridade = request.form.get('raridade')
        imagem = request.files.get('imagem')

        if imagem and imagem.filename:
            imagem_path = salvar_imagem(imagem)
        else:
            cursor.execute("SELECT imagem FROM criaturas WHERE id = %s", (id,))
            imagem_path = cursor.fetchone()['imagem']

        cursor.execute("""
            UPDATE criaturas
            SET nome = %s, elemento = %s, imagem = %s, raridade = %s
            WHERE id = %s
        """, (nome, elemento, imagem_path, raridade, id))
        conn.commit()
        conn.close()
        return redirect(url_for('criaturas'))

    cursor.execute("SELECT * FROM criaturas WHERE id = %s", (id,))
    criatura = cursor.fetchone()
    conn.close()
    return render_template('editar_criatura.html', criatura=criatura)

@app.route('/criaturas/deletar/<int:id>', methods=['GET', 'POST'])
def deletar_criatura(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("DELETE FROM criaturas WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('criaturas'))

    cursor.execute("SELECT * FROM criaturas WHERE id = %s", (id,))
    criatura = cursor.fetchone()
    conn.close()
    return render_template('confirmar_deletar_criatura.html', criatura=criatura)


# Rotas para Itens Paranormais
@app.route('/itens', methods=['GET', 'POST'])
def itens():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        elemento = request.form.get('elemento')
        efeito = request.form.get('efeito')
        raridade = request.form.get('raridade')

        cursor.execute("""
            INSERT INTO itens_paranormais (nome, elemento, efeito, raridade)
            VALUES (%s, %s, %s, %s)
        """, (nome, elemento, efeito, raridade))
        conn.commit()

    cursor.execute("SELECT * FROM itens_paranormais")
    lista_itens = cursor.fetchall()
    conn.close()
    return render_template('itens.html', itens=lista_itens)

@app.route('/itens/editar/<int:id>', methods=['GET', 'POST'])
def editar_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form.get('nome')
        elemento = request.form.get('elemento')
        efeito = request.form.get('efeito')
        raridade = request.form.get('raridade')

        cursor.execute("""
            UPDATE itens_paranormais
            SET nome = %s, elemento = %s, efeito = %s, raridade = %s
            WHERE id = %s
        """, (nome, elemento, efeito, raridade, id))
        conn.commit()
        conn.close()
        return redirect(url_for('itens'))

    cursor.execute("SELECT * FROM itens_paranormais WHERE id = %s", (id,))
    item = cursor.fetchone()
    conn.close()
    return render_template('editar_item.html', item=item)

@app.route('/itens/deletar/<int:id>', methods=['GET', 'POST'])
def deletar_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("DELETE FROM itens_paranormais WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for('itens'))

    cursor.execute("SELECT * FROM itens_paranormais WHERE id = %s", (id,))
    item = cursor.fetchone()
    conn.close()
    return render_template('confirmar_deletar_item.html', item=item)


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)