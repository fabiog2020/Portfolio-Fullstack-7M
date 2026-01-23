# services/ai_service.py
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from database import db
from models.models import User, Notification
from models.models_finance import Transacao, Categoria

class AIService:
    
    @staticmethod
    def executar_analise_geral(user: User):
        hoje = datetime.now().date()
        
        # Evita spam diário da mesma análise
        ultima_analise = Notification.query.filter(
            Notification.user_id == user.id,
            Notification.tipo == 'analysis',
            func.date(Notification.data_criacao) == hoje
        ).first()

        if ultima_analise:
            return 

        AIService._analisar_gastos_vs_mes_anterior(user)
        AIService._analisar_ofensores_de_orcamento(user)
        AIService._sugerir_investimentos(user)

    @staticmethod
    def _analisar_gastos_vs_mes_anterior(user: User):
        hoje = datetime.now()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        primeiro_dia_mes_atual = hoje.replace(day=1)
        mes_passado_data = primeiro_dia_mes_atual - timedelta(days=1)
        mes_passado = mes_passado_data.month
        ano_passado = mes_passado_data.year

        # GASTOS ATUAIS
        gastos_atual = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
            Transacao.user_id == user.id,
            Categoria.tipo == 'saída',
            extract('month', Transacao.data_transacao) == mes_atual,
            extract('year', Transacao.data_transacao) == ano_atual
        ).scalar() or 0

        # GASTOS ANTERIORES
        gastos_anterior = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
            Transacao.user_id == user.id,
            Categoria.tipo == 'saída',
            extract('month', Transacao.data_transacao) == mes_passado,
            extract('year', Transacao.data_transacao) == ano_passado
        ).scalar() or 0

        gastos_atual = abs(gastos_atual)
        gastos_anterior = abs(gastos_anterior)

        if gastos_anterior > 0:
            aumento = ((gastos_atual - gastos_anterior) / gastos_anterior) * 100
            
            if aumento > 20:
                titulo = f"⚠️ Alerta: Seus gastos subiram {int(aumento)}% este mês."
                
                detalhes = f"""
                <h3 class="font-bold text-lg mb-2">Análise de Tendência</h3>
                <p>Identificamos uma aceleração nos seus gastos em comparação ao mês passado.</p>
                <ul class="list-disc pl-5 mt-2 space-y-1">
                    <li>Gasto Mês Passado: <strong>R$ {gastos_anterior:.2f}</strong></li>
                    <li>Gasto Mês Atual: <strong>R$ {gastos_atual:.2f}</strong></li>
                    <li>Diferença: <span class="text-red-500 font-bold">+ R$ {gastos_atual - gastos_anterior:.2f}</span></li>
                </ul>
                <div class="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-500 text-yellow-700">
                    <strong>Dica da I.A.:</strong> Revise suas últimas 5 transações. Geralmente, pequenos gastos invisíveis somados causam esse impacto.
                </div>
                """
                AIService._criar_notificacao(user, titulo, "warning", detalhes=detalhes)
            
            elif aumento < -10:
                titulo = f"🏆 Parabéns! Você economizou {abs(int(aumento))}% este mês."
                
                poupado = gastos_anterior - gastos_atual
                detalhes = f"""
                <h3 class="font-bold text-lg mb-2 text-green-600">Vitória Financeira!</h3>
                <p>Você está gastando menos que no mês passado. Isso demonstra controle e disciplina.</p>
                <p class="mt-2">Valor economizado (potencial): <strong>R$ {poupado:.2f}</strong></p>
                <div class="mt-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700">
                    <strong>Sugestão:</strong> Que tal pegar esses R$ {poupado:.2f} e enviar agora para sua Meta ou Investimento? Dinheiro parado na conta corrente tende a sumir!
                </div>
                """
                AIService._criar_notificacao(user, titulo, "success", detalhes=detalhes)

    @staticmethod
    def _analisar_ofensores_de_orcamento(user: User):
        hoje = datetime.now()
        mes_atual = hoje.month
        
        keywords = ['lanche', 'restaurante', 'ifood', 'delivery', 'uber', '99', 'transporte']
        total_suporfulos = 0
        
        transacoes = db.session.query(Transacao).join(Categoria).filter(
            Transacao.user_id == user.id,
            Categoria.tipo == 'saída',
            extract('month', Transacao.data_transacao) == mes_atual
        ).all()

        for t in transacoes:
            nome_cat = t.categoria.nome.lower() if t.categoria else ""
            desc = t.descricao.lower() if t.descricao else ""
            if any(k in nome_cat for k in keywords) or any(k in desc for k in keywords):
                total_suporfulos += abs(t.valor)

        receita_total = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
            Transacao.user_id == user.id,
            Categoria.tipo == 'entrada',
            extract('month', Transacao.data_transacao) == mes_atual
        ).scalar() or 1 

        porcentagem = (total_suporfulos / receita_total) * 100
        
        if porcentagem > 20:
            titulo = f"🤖 Atenção: {int(porcentagem)}% da renda foi para Delivery/Transporte."
            
            projecao_anual = total_suporfulos * 12
            meta_sugerida = total_suporfulos * 0.3 # Cortar 30%
            
            detalhes = f"""
            <h3 class="font-bold text-lg mb-2 text-red-600">Raio-X de Gastos Supérfluos</h3>
            <p>Sua categoria de <strong>Lazer/Delivery/Transporte</strong> está consumindo uma fatia perigosa do seu orçamento.</p>
            
            <div class="grid grid-cols-2 gap-4 mt-4 mb-4">
                <div class="bg-gray-100 p-3 rounded">
                    <span class="block text-xs text-gray-500">Gasto Atual</span>
                    <span class="font-bold text-lg">R$ {total_suporfulos:.2f}</span>
                </div>
                <div class="bg-gray-100 p-3 rounded">
                    <span class="block text-xs text-gray-500">Impacto na Renda</span>
                    <span class="font-bold text-lg text-red-500">{int(porcentagem)}%</span>
                </div>
            </div>

            <div class="p-4 bg-blue-50 rounded-lg border border-blue-100">
                <h4 class="font-bold text-blue-800 mb-2">💡 Plano de Ação Inteligente</h4>
                <ul class="list-disc pl-5 space-y-2 text-sm text-blue-900">
                    <li>Se você mantiver esse ritmo, gastará <strong>R$ {projecao_anual:.2f}</strong> nisso em 1 ano.</li>
                    <li><strong>Meta de Ouro:</strong> Tente reduzir apenas 30% (R$ {meta_sugerida:.2f}).</li>
                    <li>Com essa economia, você poderia fazer uma viagem internacional a cada 2 anos.</li>
                </ul>
            </div>
            """
            AIService._criar_notificacao(user, titulo, "danger", detalhes=detalhes)

    @staticmethod
    def _sugerir_investimentos(user: User):
        saldo = AIService._calcular_saldo_atual(user)
        
        if saldo > 500:
            perfil = "conservador"
            if user.renda_mensal and user.renda_mensal > 10000:
                perfil = "arrojado"
            
            if perfil == "conservador":
                titulo = f"📈 Sobrou R$ {saldo:.2f}. Sugestão: Investimento Seguro."
                detalhes = f"""
                <h3 class="font-bold text-lg mb-2 text-green-700">Oportunidade de Investimento</h3>
                <p>Notamos que você tem um saldo positivo de <strong>R$ {saldo:.2f}</strong> parado.</p>
                <p class="mt-2">Para o seu perfil (Renda até R$ 10k), a segurança é prioridade.</p>
                
                <div class="mt-4 space-y-3">
                    <div class="p-3 border rounded hover:bg-gray-50">
                        <strong>Opção A: CDB Liquidez Diária</strong>
                        <p class="text-sm text-gray-600">Rende 100% do CDI (aprox 11% a.a.). Seguro como a Poupança, mas rende o dobro.</p>
                    </div>
                    <div class="p-3 border rounded hover:bg-gray-50">
                        <strong>Opção B: Tesouro Selic</strong>
                        <p class="text-sm text-gray-600">O investimento mais seguro do Brasil. Ideal para Reserva de Emergência.</p>
                    </div>
                </div>
                
                <div class="mt-4 text-center">
                    <a href="/investimentos" class="inline-block px-4 py-2 bg-brand-green text-white rounded font-bold">Ir para Investimentos</a>
                </div>
                """
            else:
                titulo = f"🚀 Sobrou R$ {saldo:.2f}. Oportunidade em Renda Variável."
                detalhes = f"""
                <h3 class="font-bold text-lg mb-2 text-purple-700">Potencialize seus Ganhos</h3>
                <p>Seu fluxo de caixa está saudável (Saldo: R$ {saldo:.2f}). Hora de diversificar.</p>
                
                <div class="mt-4 p-3 bg-purple-50 border-l-4 border-purple-500 text-purple-900">
                    <strong>Sugestão Arrojada:</strong> Fundos Imobiliários (FIIs) pagam aluguéis mensais isentos de imposto.
                    <br>Com esse valor, você compraria aprox. {int(saldo/10)} cotas de um fundo base 10.
                </div>
                """
                
            AIService._criar_notificacao(user, titulo, "info", detalhes=detalhes)

    @staticmethod
    def _calcular_saldo_atual(user):
        receitas = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
            Transacao.user_id == user.id, Categoria.tipo == 'entrada'
        ).scalar() or 0
        despesas = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
            Transacao.user_id == user.id, Categoria.tipo == 'saída'
        ).scalar() or 0
        # Investimentos entram como saída de caixa na visão de saldo disponível
        investido = db.session.query(func.sum(Transacao.valor)).join(Categoria).filter(
            Transacao.user_id == user.id, Categoria.tipo == 'investimento'
        ).scalar() or 0
        
        return receitas - abs(despesas) - abs(investido)

    @staticmethod
    def _criar_notificacao(user, mensagem, tipo, link=None, detalhes=None):
        notif = Notification(
            user_id=user.id,
            mensagem=mensagem,
            tipo='analysis' if detalhes else tipo, # Se tem detalhes, é análise. Se não, é aviso simples.
            link_destino=link,
            detalhes=detalhes # Salvando o HTML gerado
        )
        db.session.add(notif)
        db.session.commit()