from datetime import date, datetime, timedelta
import calendar
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from database import db
from models import Transacao, Categoria, Cartao, Parcela
from forms.transacao_form import TransacaoForm

from services.transactions_service import criar_transacao_a_partir_formulario
from services.import_service import ImportService 

transactions_bp = Blueprint('transactions', __name__)

# =========================================================
# GESTÃO (EXTRATO + DESFAZER + FILTROS)
# =========================================================

@transactions_bp.route("/extrato", methods=["GET"])
@login_required
def extrato():
    """
    Lista transações/parcelas com FILTRO DE DATA e painel de Rollback.
    """
    # 1. DEFINIR DATAS DO FILTRO (Padrão: Mês Atual)
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str = request.args.get('data_fim')
    
    hoje = date.today()

    if data_inicio_str and data_fim_str:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
    else:
        # Se não vier filtro, pega o primeiro e último dia do mês atual
        data_inicio = date(hoje.year, hoje.month, 1)
        last_day = calendar.monthrange(hoje.year, hoje.month)[1]
        data_fim = date(hoje.year, hoje.month, last_day)

    # Converter para datetime (inicio do dia e fim do dia) para busca no banco
    dt_start = datetime.combine(data_inicio, datetime.min.time())
    dt_end = datetime.combine(data_fim, datetime.max.time())

    # 2. BUSCAR DADOS (Aplicando o Filtro)
    
    # Transações (Conta Corrente)
    transacoes = Transacao.query.filter(
        Transacao.user_id == current_user.id,
        Transacao.data_transacao >= dt_start,
        Transacao.data_transacao <= dt_end
    ).order_by(Transacao.data_transacao.desc()).all()
    
    # Parcelas (Cartão)
    parcelas = Parcela.query.filter(
        Parcela.user_id == current_user.id,
        Parcela.data_vencimento >= dt_start,
        Parcela.data_vencimento <= dt_end
    ).order_by(Parcela.data_vencimento.desc()).all()

    # 3. UNIFICAR LISTA
    lista_completa = []
    importacoes_set = set() # Para identificar os lotes únicos (para o botão desfazer)

    for t in transacoes:
        t.tipo_origem = 'transacao'
        lista_completa.append(t)
        if t.import_id:
            try:
                parts = t.import_id.split('_')
                d = parts[1]; h = parts[2]
                display = f"Importação de {d[6:8]}/{d[4:6]} às {h[0:2]}:{h[2:4]}"
                importacoes_set.add((t.import_id, display))
            except: pass
        
    for p in parcelas:
        p.tipo_origem = 'parcela'
        p.data_transacao = p.data_vencimento 
        lista_completa.append(p)
        if p.import_id:
            try:
                parts = p.import_id.split('_')
                d = parts[1]; h = parts[2]
                display = f"Importação de {d[6:8]}/{d[4:6]} às {h[0:2]}:{h[2:4]}"
                importacoes_set.add((p.import_id, display))
            except: pass

    # Ordena lista por data
    lista_completa.sort(key=lambda x: x.data_transacao, reverse=True)
    
    # Ordena importações (mais recente primeiro)
    lista_importacoes = sorted(list(importacoes_set), key=lambda x: x[0], reverse=True)

    return render_template(
        "extrato.html", 
        movimentacoes=lista_completa, 
        importacoes=lista_importacoes,
        data_inicio=data_inicio, # Passa para o HTML manter o valor no input
        data_fim=data_fim
    )


@transactions_bp.route("/desfazer_importacao/<batch_id>", methods=["POST"])
@login_required
def desfazer_importacao(batch_id):
    try:
        t_del = Transacao.query.filter_by(user_id=current_user.id, import_id=batch_id).delete()
        p_del = Parcela.query.filter_by(user_id=current_user.id, import_id=batch_id).delete()
        
        db.session.commit()
        
        total = t_del + p_del
        if total > 0:
            flash(f"Importação desfeita com sucesso! {total} itens removidos.", "success")
        else:
            flash("Nenhum item encontrado para desfazer.", "warning")
            
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao desfazer: {e}", "danger")

    return redirect(url_for("transactions.extrato"))


@transactions_bp.route("/excluir_massa", methods=["POST"])
@login_required
def excluir_em_massa():
    itens_selecionados = request.form.getlist("selecionados")
    if not itens_selecionados:
        flash("Nada selecionado.", "warning")
        return redirect(url_for("transactions.extrato"))

    try:
        cont = 0
        for item_str in itens_selecionados:
            tipo, id_str = item_str.split("_")
            id_num = int(id_str)
            
            obj = None
            if tipo == 'transacao': obj = db.session.get(Transacao, id_num)
            elif tipo == 'parcela': obj = db.session.get(Parcela, id_num)
            
            if obj and obj.user_id == current_user.id:
                db.session.delete(obj)
                cont += 1
        
        db.session.commit()
        flash(f"{cont} itens excluídos.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro: {e}", "danger")

    return redirect(url_for("transactions.extrato"))


# =========================================================
# ROTAS ADICIONAR / EDITAR / EXCLUIR SINGLE
# =========================================================

@transactions_bp.route("/adicionar", methods=["GET"])
@login_required
def formulario_adicionar_transacao():
    form = TransacaoForm()
    categorias = Categoria.query.filter_by(user_id=current_user.id).order_by(Categoria.nome.asc()).all()
    categorias_transacao = [c for c in categorias if c.tipo in ["entrada", "saída"]]
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    
    choices = [(0, 'Conta Corrente / Dinheiro')] + [(c.id, c.nome) for c in cartoes]
    form.cartao_import_id.choices = choices
    return render_template("adicionar.html", form=form, categorias=categorias_transacao, cartoes=cartoes)

@transactions_bp.route("/adicionar", methods=["POST"])
@login_required
def adicionar_transacao():
    form = TransacaoForm()
    cartoes = Cartao.query.filter_by(user_id=current_user.id).all()
    form.cartao_import_id.choices = [(0, 'Conta Corrente / Dinheiro')] + [(c.id, c.nome) for c in cartoes]

    if not form.validate_on_submit():
        return redirect(url_for("transactions.formulario_adicionar_transacao"))

    # IMPORTAÇÃO
    if form.arquivo.data:
        arquivo = form.arquivo.data
        filename = arquivo.filename.lower()
        senha = form.senha_pdf.data
        cartao_id = form.cartao_import_id.data if form.cartao_import_id.data != 0 else None
        
        try: cat_padrao = int(request.form.get('categoria_id'))
        except: cat_padrao = 1
        
        if filename.endswith('.ofx'):
            sucesso, msg = ImportService.processar_ofx(arquivo, current_user.id, cat_padrao, cartao_id)
        elif filename.endswith('.csv'):
            sucesso, msg = ImportService.processar_csv(arquivo, current_user.id, cat_padrao, cartao_id)
        elif filename.endswith('.pdf'):
            sucesso, msg = ImportService.processar_pdf(arquivo, current_user.id, cat_padrao, senha, cartao_id)
        else:
            sucesso, msg = False, "Formato não suportado."

        if sucesso:
            flash(msg, "success")
            return redirect(url_for("transactions.extrato")) 
        else:
            flash(msg, "danger")
            return redirect(url_for("transactions.formulario_adicionar_transacao"))

    # MANUAL
    if not form.valor.data or not form.data.data:
        flash("Manual: Valor e Data obrigatórios.", "warning")
        return redirect(url_for("transactions.formulario_adicionar_transacao"))

    if criar_transacao_a_partir_formulario(form):
        return redirect(url_for("main.dashboard"))
    
    return redirect(url_for("transactions.formulario_adicionar_transacao"))

@transactions_bp.route("/excluir/<int:id>", methods=["POST"])
@login_required
def excluir_transacao(id):
    item = Transacao.query.filter_by(id=id, user_id=current_user.id).first()
    if not item:
        item = Parcela.query.filter_by(id=id, user_id=current_user.id).first()
    
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Excluído.", "success")
    return redirect(request.referrer or url_for("main.dashboard"))

@transactions_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_transacao(id):
    transacao = Transacao.query.filter_by(id=id, user_id=current_user.id).first()
    if not transacao:
        flash("Transação não encontrada.", "danger")
        return redirect(url_for("main.dashboard"))

    categorias = Categoria.query.filter_by(user_id=current_user.id).filter(Categoria.tipo.in_(["entrada", "saída"])).order_by(Categoria.nome.asc()).all()

    if request.method == "POST":
        try:
            categoria_id = int(request.form.get("categoria_id"))
            descricao = request.form.get("descricao")
            valor = float(request.form.get("valor"))
            data_transacao = date.fromisoformat(request.form.get("data"))
            
            nova_categoria = Categoria.query.get(categoria_id)
            valor_final = valor
            if nova_categoria.tipo == "saída": valor_final = -abs(valor)
            elif nova_categoria.tipo == "entrada": valor_final = abs(valor)

            transacao.categoria_id = categoria_id
            transacao.descricao = descricao
            transacao.valor = valor_final
            transacao.data_transacao = data_transacao
            
            db.session.commit()
            flash("Atualizado!", "success")
            return redirect(url_for("main.dashboard"))
        except: pass

    return render_template("editar.html", transacao=transacao, categorias=categorias)