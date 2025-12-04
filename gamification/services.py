# gamification/services.py
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import (
    PerfilGamificacao, Conquista, ConquistaUsuario, 
    Desafio, DesafioUsuario, HistoricoGamificacao,
    NivelFinanceiro
)


class GamificacaoService:
    """Serviço centralizado para lógica de gamificação"""
    
    @staticmethod
    def inicializar_perfil(user):
        """Cria o perfil de gamificação para um novo usuário"""
        perfil, criado = PerfilGamificacao.objects.get_or_create(user=user)
        
        if criado:
            # Configura nível inicial
            nivel_inicial = NivelFinanceiro.objects.filter(numero=1).first()
            perfil.nivel_atual = nivel_inicial
            perfil.save()
            
            # Bônus de boas-vindas
            perfil.adicionar_pontos(50, "Boas-vindas ao Nebue! 🎉")
        
        return perfil
    
    @staticmethod
    def registrar_transacao(user, transacao):
        """Registra uma transação e verifica conquistas relacionadas"""
        perfil = GamificacaoService.inicializar_perfil(user)
        
        # Atualiza streak
        streak_mantido = perfil.atualizar_streak()
        
        # Pontos base por registrar transação
        perfil.adicionar_pontos(5, "Registrou uma transação")
        
        # Verifica conquistas de disciplina
        GamificacaoService.verificar_conquistas_disciplina(perfil)
        
        # Verifica conquistas específicas de economia/gasto
        if transacao.tipo == 'receita':
            GamificacaoService.verificar_conquistas_receita(perfil, transacao)
        else:
            GamificacaoService.verificar_conquistas_despesa(perfil, transacao)
        
        return perfil
    
    @staticmethod
    def verificar_conquistas_disciplina(perfil):
        """Verifica conquistas relacionadas à disciplina de registro"""
        conquistas = {
            7: 'Primeira Semana Completa',
            30: 'Um Mês de Controle',
            90: 'Trimestre Disciplinado',
            365: 'Ano de Ouro',
        }
        
        if perfil.streak_atual in conquistas:
            titulo = conquistas[perfil.streak_atual]
            conquista = Conquista.objects.filter(titulo=titulo).first()
            
            if conquista:
                obj, criado = ConquistaUsuario.objects.get_or_create(
                    perfil=perfil,
                    conquista=conquista
                )
                
                if criado:
                    perfil.adicionar_pontos(conquista.pontos, f"Conquista: {titulo}!")
                    perfil.conquistas_desbloqueadas += 1
                    perfil.save()
                    
                    HistoricoGamificacao.objects.create(
                        perfil=perfil,
                        tipo='conquista',
                        descricao=f"Desbloqueou: {titulo}",
                        pontos=conquista.pontos
                    )
    
    @staticmethod
    def verificar_conquistas_receita(perfil, transacao):
        """Verifica conquistas relacionadas a receitas"""
        from transactions.models import Transaction  # Ajuste o import conforme seu projeto
        
        total_receitas = Transaction.objects.filter(
            user=perfil.user,
            tipo='receita'
        ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
        
        marcos = [
            (Decimal('1000'), 'Primeiros Mil'),
            (Decimal('5000'), 'Cinco Mil Acumulados'),
            (Decimal('10000'), 'Dez Mil em Receitas'),
            (Decimal('50000'), 'Cinquenta Mil!'),
        ]
        
        for valor, titulo in marcos:
            if total_receitas >= valor:
                conquista = Conquista.objects.filter(titulo=titulo).first()
                if conquista:
                    obj, criado = ConquistaUsuario.objects.get_or_create(
                        perfil=perfil,
                        conquista=conquista
                    )
                    if criado:
                        perfil.adicionar_pontos(conquista.pontos, f"Conquista: {titulo}!")
    
    @staticmethod
    def verificar_conquistas_despesa(perfil, transacao):
        """Verifica conquistas relacionadas a controle de despesas"""
        # Implementar lógica específica para despesas
        pass
    
    @staticmethod
    def verificar_conquista_meta(perfil, meta):
        """Verifica conquistas ao completar uma meta"""
        conquista = Conquista.objects.filter(titulo='Primeira Meta Alcançada').first()
        
        if conquista:
            obj, criado = ConquistaUsuario.objects.get_or_create(
                perfil=perfil,
                conquista=conquista
            )
            if criado:
                perfil.adicionar_pontos(conquista.pontos, "Completou sua primeira meta! 🎯")
    
    @staticmethod
    def verificar_conquista_reserva(perfil, valor_reserva):
        """Verifica conquistas relacionadas à reserva de emergência"""
        marcos_reserva = [
            (Decimal('500'), 'Primeira Reserva'),
            (Decimal('1000'), 'Mil Guardados'),
            (Decimal('5000'), 'Reserva Sólida'),
            (Decimal('10000'), 'Reserva de Elite'),
        ]
        
        for valor, titulo in marcos_reserva:
            if valor_reserva >= valor:
                conquista = Conquista.objects.filter(titulo=titulo).first()
                if conquista:
                    obj, criado = ConquistaUsuario.objects.get_or_create(
                        perfil=perfil,
                        conquista=conquista
                    )
                    if criado:
                        perfil.adicionar_pontos(conquista.pontos, f"Conquista: {titulo}! 💰")
    
    @staticmethod
    def atualizar_desafios(perfil):
        """Atualiza o progresso de todos os desafios ativos do usuário"""
        desafios_ativos = DesafioUsuario.objects.filter(
            perfil=perfil,
            status='em_andamento',
            desafio__status='ativo'
        )
        
        for desafio_usuario in desafios_ativos:
            # Verifica se o desafio ainda está no prazo
            if not desafio_usuario.desafio.esta_ativo():
                desafio_usuario.status = 'falhado'
                desafio_usuario.save()
                continue
            
            # Atualiza progresso baseado no tipo de desafio
            GamificacaoService.calcular_progresso_desafio(desafio_usuario)
    
    @staticmethod
    def calcular_progresso_desafio(desafio_usuario):
        """Calcula o progresso atual de um desafio"""
        desafio = desafio_usuario.desafio
        perfil = desafio_usuario.perfil
        
        if desafio.meta_tipo == 'economia':
            # Calcula quanto o usuário economizou no período
            from transactions.models import Transaction
            
            economia = Transaction.objects.filter(
                user=perfil.user,
                tipo='receita',
                data__gte=desafio.data_inicio,
                data__lte=desafio.data_fim
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
            
            gastos = Transaction.objects.filter(
                user=perfil.user,
                tipo='despesa',
                data__gte=desafio.data_inicio,
                data__lte=desafio.data_fim
            ).aggregate(total=Sum('valor'))['total'] or Decimal('0')
            
            economia_real = economia - gastos
            desafio_usuario.atualizar_progresso(max(0, economia_real))
        
        elif desafio.meta_tipo == 'reduzir_gastos':
            # Compara gastos com período anterior
            pass  # Implementar lógica de comparação
        
        elif desafio.meta_tipo == 'investimento':
            # Verifica investimentos realizados
            pass  # Implementar quando tiver módulo de investimentos
    
    @staticmethod
    def get_ranking(periodo='mensal', limite=10):
        """Retorna o ranking de usuários"""
        hoje = timezone.now().date()
        
        if periodo == 'semanal':
            data_inicio = hoje - timedelta(days=7)
        elif periodo == 'mensal':
            data_inicio = hoje - timedelta(days=30)
        else:
            data_inicio = None
        
        query = PerfilGamificacao.objects.select_related('user', 'nivel_atual')
        
        if data_inicio:
            # Calcula pontos no período
            query = query.annotate(
                pontos_periodo=Sum(
                    'historico__pontos',
                    filter=Q(historico__criado_em__gte=data_inicio)
                )
            ).order_by('-pontos_periodo')
        else:
            query = query.order_by('-pontos_totais')
        
        return query[:limite]
    
    @staticmethod
    def get_conquistas_nao_visualizadas(perfil):
        """Retorna conquistas não visualizadas"""
        return ConquistaUsuario.objects.filter(
            perfil=perfil,
            visualizada=False
        ).select_related('conquista', 'conquista__tipo')
    
    @staticmethod
    def marcar_conquistas_visualizadas(perfil):
        """Marca todas as conquistas como visualizadas"""
        ConquistaUsuario.objects.filter(
            perfil=perfil,
            visualizada=False
        ).update(visualizada=True)
    
    @staticmethod
    def criar_desafio_personalizado(perfil, tipo_meta, valor_meta, dias=30):
        """Cria um desafio personalizado para o usuário"""
        hoje = timezone.now().date()
        
        desafio = Desafio.objects.create(
            titulo=f"Desafio Personalizado - {tipo_meta}",
            descricao=f"Alcance {tipo_meta} de R$ {valor_meta} em {dias} dias",
            periodo='personalizado',
            meta_tipo=tipo_meta,
            meta_valor=valor_meta,
            pontos_recompensa=100,
            data_inicio=hoje,
            data_fim=hoje + timedelta(days=dias),
            publico=False
        )
        
        desafio_usuario = DesafioUsuario.objects.create(
            perfil=perfil,
            desafio=desafio
        )
        
        return desafio_usuario
    
    @staticmethod
    def get_estatisticas(perfil):
        """Retorna estatísticas completas do perfil"""
        return {
            'pontos_totais': perfil.pontos_totais,
            'nivel': {
                'numero': perfil.nivel_atual.numero if perfil.nivel_atual else 0,
                'nome': perfil.nivel_atual.nome if perfil.nivel_atual else 'Iniciante',
                'progresso': perfil.progresso_nivel()
            },
            'streak': {
                'atual': perfil.streak_atual,
                'maior': perfil.maior_streak
            },
            'conquistas': {
                'total': perfil.conquistas_desbloqueadas,
                'nao_visualizadas': perfil.conquistas.filter(visualizada=False).count()
            },
            'desafios': {
                'completados': perfil.desafios_completados,
                'em_andamento': perfil.desafios.filter(status='em_andamento').count()
            }
        }