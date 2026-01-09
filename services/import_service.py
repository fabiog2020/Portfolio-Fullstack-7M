import pandas as pd
import pdfplumber
import re
import uuid
import unicodedata
from ofxparse import OfxParser
from datetime import datetime
from database import db
from models import Categoria, Transacao, Parcela
from services.transactions_service import adicionar_transacao_core

class ImportService:
    
    @staticmethod
    def normalizar_texto(texto):
        """
        Remove acentos e deixa minúsculo para facilitar a comparação.
        Ex: 'Alimentação' vira 'alimentacao'
        """
        if not texto: return ""
        return ''.join(c for c in unicodedata.normalize('NFD', texto)
                  if unicodedata.category(c) != 'Mn').lower()

    @staticmethod
    def identificar_categoria(descricao, user_id):
        """
        Categorização Inteligente Turbinada.
        """
        desc_norm = ImportService.normalizar_texto(descricao)

        # MAPA: Palavra Chave -> Lista de Possíveis Categorias (Tenta achar uma delas)
        mapa_inteligente = {
            # ALIMENTAÇÃO
            ('food', 'ifood', 'rappi', 'ubereats', 
             'restaurante', 'padaria', 'panificadora', 'lanche', 'pizza', 
             'burguer', 'churrascaria', 'sabor', 'fome', 'lanchonete',
              'costela', 'refeicao', 'marmita'): 
             ['Alimentação', 'Comida', 'Restaurante'],

             #supermercado
            ('diaadia', 'gbarbosa', 'big','supermercado', 'loja', 'mercadinho', 'hortifruti', 'bompreco', 'assai', 'atacadao', 'extra',
             'carrefour', 'pao de acucar', 'pernambucanas'):
             ['Alimentação', 'Mercado', 'Comida', 'Restaurante'],


            # TRANSPORTE
            ('uber', '99', 'taxi', 'br', 'estacionamento', 'sem parar', 
             'pedagio', 'veloe', 'onibus', 'metro', 'passagem'):
             ['Transporte', 'Combustível', 'Carro', 'Locomoção'],

             #COMBUSTIVEL
            ('gasolina', 'diesel', 'alcool', 'etanol','oleo','lubrificante','oficina', 'posto', 'ipiranga', 'shell', 'br', 'petrobras'):
             ['Combustível', 'Carro', 'Transporte'],

            # SAÚDE
            ('farmacia', 'drogaria', 'pague menos', 'drogasil', 'medico', 
             'hospital', 'doutor', 'clinica', 'exame', 'laboratorio', 'dentista'):
             ['Saúde', 'Medicamentos', 'Médico'],

            # EDUCAÇÃO
            ('curso', 'udemy', 'alura', 'hotmart', 'kiwify', 'escola', 'colegio', 
             'faculdade', 'universidade', 'mensalidade', 'leitura', 'livraria', 'papelaria'):
             ['Educação', 'Estudos', 'Cursos', 'Escola'],

            # LAZER
            ('netflix', 'spotify', 'prime', 'hbo', 'disney', 'cinema', 'ingresso', 
             'show', 'bebida', 'adega', 'bar', 'cerveja', 'pub', 'club', 'jogo', 'steam'):
             ['Lazer', 'Entretenimento', 'Assinaturas'],

            # COMPRAS / VESTUÁRIO
            ('Roupas','roupas', 'compras', 'moda', 'vestuario', 'zara','shopee', 'amazon', 'temu','aliexpress', 'renner', 'riachuelo', 'cea', 
             'shein', 'loja', 'sapato', 'tenis', 'nike', 'adidas', 'shopping'):
             ['Vestuário', 'Roupas', 'Compras', 'Pessoal'],

            # CASA / ELETRÔNICOS
            ('casas bahia', 'magalu', 'magazine', 'ponto frio', 'fast shop', 
             'samsung', 'apple', 'amazon', 'mercadolivre', 'eletro', 'moveis', 'leroy'):
             ['Casa', 'Eletrônicos', 'Compras', 'Moradia'],

            # SALÁRIO
            ('salario', 'pagamento', 'credito', 'proventos', 'remuneracao', 'pix recebido'):
             ['Salário', 'Receita', 'Entradas']
        }

        # 1. Busca por Palavras-Chave
        for palavras_chave, categorias_alvo in mapa_inteligente.items():
            for palavra in palavras_chave:
                if palavra in desc_norm:
                    # Se achou a palavra (ex: "roupa"), tenta achar uma categoria compatível no banco
                    for alvo in categorias_alvo:
                        cat_banco = db.session.query(Categoria).filter_by(user_id=user_id).filter(
                            Categoria.nome.ilike(f"%{alvo}%") # Busca flexível (case insensitive)
                        ).first()
                        if cat_banco:
                            return cat_banco.id

        # 2. Busca pelo Nome da Categoria dentro da Descrição (Fallback)
        # Ex: Se a descrição é "Pagamento Aluguel" e existe categoria "Aluguel"
        categorias_user = db.session.query(Categoria).filter_by(user_id=user_id).all()
        for cat in categorias_user:
            if ImportService.normalizar_texto(cat.nome) in desc_norm:
                return cat.id
        
        return None

    @staticmethod
    def verificar_duplicidade(user_id, descricao, valor, data, cartao_id=None):
        margem = 0.01
        if cartao_id:
            existe = Parcela.query.filter_by(user_id=user_id, cartao_id=cartao_id, descricao=descricao, data_vencimento=data)\
                .filter(Parcela.valor >= valor - margem, Parcela.valor <= valor + margem).first()
        else:
            existe = Transacao.query.filter_by(user_id=user_id, descricao=descricao, data_transacao=data)\
                .filter(Transacao.valor >= valor - margem, Transacao.valor <= valor + margem).first()
        return existe is not None

    @staticmethod
    def salvar_item_importado(user_id, categoria_id, descricao, valor, data, cartao_id=None, batch_id=None):
        try:
            # Verifica duplicidade
            valor_check = abs(valor) if cartao_id else valor
            if ImportService.verificar_duplicidade(user_id, descricao, valor_check, data, cartao_id):
                return True, "Duplicado"

            if cartao_id:
                nova = Parcela(
                    user_id=user_id,
                    categoria_id=categoria_id,
                    cartao_id=cartao_id,
                    descricao=descricao,
                    valor=abs(valor),
                    data_vencimento=data,
                    pago=False,
                    import_id=batch_id
                )
                db.session.add(nova)
            else:
                nova = Transacao(
                    user_id=user_id,
                    categoria_id=categoria_id,
                    descricao=descricao,
                    valor=valor,
                    data_transacao=data,
                    import_id=batch_id
                )
                db.session.add(nova)

            db.session.commit()
            return True, "Salvo"
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    # ==========================================
    # PROCESSADORES
    # ==========================================

    @staticmethod
    def processar_pdf(file_storage, user_id, categoria_padrao_id, senha=None, cartao_id=None):
        batch_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        try:
            count = 0
            ignorado = 0
            try: pdf = pdfplumber.open(file_storage, password=senha or "")
            except: return False, "Erro senha PDF."

            ano_fatura = datetime.now().year
            texto_full = ""
            with pdf:
                for p in pdf.pages:
                    t = p.extract_text()
                    if t: texto_full += t + "\n"
            match_ano = re.search(r'Vencimento[:\s].*?(\d{2}/\d{2}/(\d{4}))', texto_full)
            if match_ano: ano_fatura = int(match_ano.group(2))

            with pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    for linha in text.split('\n'):
                        regex_itau = r'(\d{2}/\d{2})\s+(.*?)\s+(-?[\d\.]+,\d{2})'
                        for match in re.finditer(regex_itau, linha):
                            dia_mes, desc, val_str = match.groups()
                            
                            desc_lower = desc.lower()
                            if "total" in desc_lower or "saldo" in desc_lower or "pagamento" in desc_lower: continue

                            data_str = f"{dia_mes}/{ano_fatura}"
                            try: data_t = datetime.strptime(data_str, "%d/%m/%Y")
                            except: continue

                            val_limpo = val_str.replace('.', '').replace(',', '.')
                            try: valor = float(val_limpo)
                            except: continue

                            if "-" in desc or "crédito" in desc_lower: valor = -abs(valor)

                            cat_id = ImportService.identificar_categoria(desc, user_id) or categoria_padrao_id
                            
                            sucesso, msg = ImportService.salvar_item_importado(
                                user_id, cat_id, desc.strip(), valor, data_t, cartao_id, batch_id=batch_id
                            )
                            if sucesso:
                                if "Duplicado" in msg: ignorado += 1
                                else: count += 1
            return True, f"{count} novos itens PDF. ({ignorado} ignorados). Lote: {batch_id}"
        except Exception as e:
            return False, f"Erro PDF: {e}"

    @staticmethod
    def processar_ofx(file_storage, user_id, categoria_padrao_id, cartao_id=None):
        batch_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        try:
            ofx = OfxParser.parse(file_storage)
            count = 0
            ignorado = 0
            for trans in ofx.account.statement.transactions:
                cat_id = ImportService.identificar_categoria(trans.memo, user_id) or categoria_padrao_id
                
                sucesso, msg = ImportService.salvar_item_importado(
                    user_id, cat_id, trans.memo, float(trans.amount), trans.date, cartao_id, batch_id=batch_id
                )
                if sucesso:
                    if "Duplicado" in msg: ignorado += 1
                    else: count += 1
            return True, f"{count} novos itens OFX. Lote: {batch_id}"
        except Exception as e:
            return False, f"Erro OFX: {str(e)}"

    @staticmethod
    def processar_csv(file_storage, user_id, categoria_padrao_id, cartao_id=None):
        batch_id = f"imp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        try:
            df = pd.read_csv(file_storage)
            cols = {c.lower(): c for c in df.columns}
            col_data = next((v for k, v in cols.items() if 'data' in k or 'date' in k), None)
            col_desc = next((v for k, v in cols.items() if 'desc' in k or 'memo' in k), None)
            col_valor = next((v for k, v in cols.items() if 'valor' in k or 'amount' in k), None)

            if not (col_data and col_desc and col_valor): return False, "CSV inválido."

            count = 0
            ignorado = 0
            for _, row in df.iterrows():
                try:
                    data_t = pd.to_datetime(row[col_data]).to_pydatetime()
                    desc = str(row[col_desc])
                    valor = float(str(row[col_valor]).replace(',', '.'))
                    cat_id = ImportService.identificar_categoria(desc, user_id) or categoria_padrao_id
                    
                    sucesso, msg = ImportService.salvar_item_importado(
                        user_id, cat_id, desc, valor, data_t, cartao_id, batch_id=batch_id
                    )
                    if sucesso:
                        if "Duplicado" in msg: ignorado += 1
                        else: count += 1
                except: continue
            return True, f"{count} novos itens CSV. Lote: {batch_id}"
        except Exception as e: return False, str(e)