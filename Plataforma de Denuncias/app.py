from flask import Flask, render_template, request, redirect, url_for, flash, session
import secrets
import string
import datetime

app = Flask(__name__)
app.secret_key = "chave_secreta_para_sessoes_e_flashes"

DENUNCIAS_DB = {}
USUARIOS_DB = {
    "usuario@email.com": {
        "nome": "Usuário Exemplo",
        "email": "usuario@email.com",
        "senha": "123",
        "role": "user"
    },
    "admin@protecao.org": {
        "nome": "Administrador",
        "email": "admin@protecao.org",
        "senha": "admin",
        "role": "admin"
    }
}

def gerar_protocolo():
    ano = datetime.datetime.now().year
    sufixo = ''.join(secrets.choice(string.digits) for _ in range(6))
    return f"{ano}-{sufixo}"

def gerar_codigo_acompanhamento():
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        
        user = USUARIOS_DB.get(email)
        if user and user['senha'] == senha:
            session['user_id'] = user['email']
            session['user_name'] = user['nome']
            session['user_role'] = user['role']
            flash(f"Bem-vindo(a), {user['nome']}!", "success")
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("E-mail ou senha incorretos.", "error")
            
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha')
        
        if email in USUARIOS_DB:
            flash("E-mail já cadastrado.", "error")
            return redirect(url_for('cadastro'))
            
        USUARIOS_DB[email] = {
            "nome": nome,
            "email": email,
            "senha": senha,
            "role": "user"
        }
        flash("Cadastro realizado com sucesso! Faça login para continuar.", "success")
        return redirect(url_for('login'))
        
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for('index'))

@app.route('/denunciar', methods=['GET', 'POST'])
def registrar_denuncia():
    if request.method == 'POST':
        categoria = request.form.get('categoria')
        descricao = request.form.get('descricao')
        data_hora = request.form.get('data_hora')
        localizacao = request.form.get('localizacao')
        municipio_uf = request.form.get('municipio_uf')
        

        if 'user_id' in session:
            opcao_anonimo = request.form.get('anonimo') == 'true'
            denunciante_email = None if opcao_anonimo else session['user_id']
        else:
            opcao_anonimo = True
            denunciante_email = None

        if not categoria or not descricao or not localizacao:
            flash("Preencha todos os campos obrigatórios.", "error")
            return redirect(url_for('registrar_denuncia'))

        protocolo = gerar_protocolo()
        codigo_segredo = gerar_codigo_acompanhamento()

        DENUNCIAS_DB[protocolo] = {
            'protocolo': protocolo,
            'codigo': codigo_segredo,
            'categoria': categoria,
            'descricao': descricao,
            'data_hora': data_hora,
            'localizacao': localizacao,
            'municipio_uf': municipio_uf,
            'anonimo': opcao_anonimo,
            'denunciante_email': denunciante_email, 
            'status': 'Recebida',
            'data_registro': datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
            'mensagem_publica': 'Denúncia registrada com sucesso. Aguardando triagem.'
        }

        return render_template('confirmacao.html', protocolo=protocolo, codigo=codigo_segredo)

    return render_template('denunciar.html')

@app.route('/acompanhar', methods=['GET', 'POST'])
def acompanhar_denuncia():
    resultado = None
    erro = None

    if request.method == 'POST':
        protocolo = request.form.get('protocolo', '').strip()
        codigo = request.form.get('codigo', '').strip()

        denuncia = DENUNCIAS_DB.get(protocolo)

        if denuncia and denuncia['codigo'] == codigo:
            resultado = {
                'status': denuncia['status'],
                'data_registro': denuncia['data_registro'],
                'mensagem': denuncia['mensagem_publica']
            }
        else:
            erro = "Protocolo ou código de acompanhamento inválido."

    return render_template('acompanhar.html', resultado=resultado, erro=erro)

@app.route('/minhas-denuncias')
def minhas_denuncias():
    if 'user_id' not in session:
        flash("Faça login para visualizar suas denúncias.", "warning")
        return redirect(url_for('login'))
        
    user_email = session['user_id']
    minhas = [d for d in DENUNCIAS_DB.values() if d.get('denunciante_email') == user_email]
    return render_template('minhas_denuncias.html', denuncias=minhas)

@app.route('/adocao')
def adocao_publica():
    return render_template('adocao.html')

# Área Administrativa (RF006, RF008, RS003)
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_role') != 'admin':
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for('login'))
    
    total = len(DENUNCIAS_DB)
    recebidas = sum(1 for d in DENUNCIAS_DB.values() if d['status'] == 'Recebida')
    
    return render_template('admin/dashboard.html', total=total, recebidas=recebidas)

@app.route('/admin/denuncias')
def admin_denuncias():
    if session.get('user_role') != 'admin':
        flash("Acesso restrito a administradores.", "error")
        return redirect(url_for('login'))
        
    return render_template('admin/denuncias.html', denuncias=list(DENUNCIAS_DB.values()))

if __name__ == '__main__':
    app.run(debug=True)
