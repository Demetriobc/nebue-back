# gamification/management/commands/popular_gamificacao.py
from django.core.management.base import BaseCommand
from gamification.models import NivelFinanceiro, TipoConquista, Conquista


class Command(BaseCommand):
    help = 'Popula o banco de dados com níveis e conquistas iniciais'

    def handle(self, *args, **kwargs):
        self.stdout.write('Criando níveis financeiros...')
        self.criar_niveis()
        
        self.stdout.write('Criando tipos de conquistas...')
        self.criar_tipos_conquistas()
        
        self.stdout.write('Criando conquistas...')
        self.criar_conquistas()
        
        self.stdout.write(self.style.SUCCESS('✅ Gamificação populada com sucesso!'))

    def criar_niveis(self):
        niveis = [
            {
                'numero': 1,
                'nome': 'Aprendiz Financeiro',
                'descricao': 'Você está começando sua jornada rumo à estabilidade financeira',
                'pontos_necessarios': 0,
                'icone': 'fa-seedling',
                'cor': '#9E9E9E'
            },
            {
                'numero': 2,
                'nome': 'Organizador Consciente',
                'descricao': 'Você já domina o básico da organização financeira',
                'pontos_necessarios': 500,
                'icone': 'fa-book',
                'cor': '#2196F3'
            },
            {
                'numero': 3,
                'nome': 'Poupador Estratégico',
                'descricao': 'Você sabe poupar e planejar o futuro',
                'pontos_necessarios': 1500,
                'icone': 'fa-piggy-bank',
                'cor': '#9C27B0'
            },
            {
                'numero': 4,
                'nome': 'Investidor Iniciante',
                'descricao': 'Você está pronto para fazer seu dinheiro trabalhar',
                'pontos_necessarios': 3500,
                'icone': 'fa-chart-line',
                'cor': '#FF9800'
            },
            {
                'numero': 5,
                'nome': 'Mestre das Finanças',
                'descricao': 'Você alcançou a excelência financeira!',
                'pontos_necessarios': 7500,
                'icone': 'fa-crown',
                'cor': '#FFD700'
            },
        ]
        
        for nivel_data in niveis:
            NivelFinanceiro.objects.get_or_create(
                numero=nivel_data['numero'],
                defaults=nivel_data
            )

    def criar_tipos_conquistas(self):
        tipos = [
            {
                'categoria': 'economia',
                'nome': 'Economia',
                'icone': 'fa-piggy-bank',
                'cor': '#4CAF50'
            },
            {
                'categoria': 'organizacao',
                'nome': 'Organização',
                'icone': 'fa-list-check',
                'cor': '#2196F3'
            },
            {
                'categoria': 'investimento',
                'nome': 'Investimento',
                'icone': 'fa-chart-line',
                'cor': '#FF9800'
            },
            {
                'categoria': 'quitacao',
                'nome': 'Quitação de Dívidas',
                'icone': 'fa-hand-holding-dollar',
                'cor': '#9C27B0'
            },
            {
                'categoria': 'disciplina',
                'nome': 'Disciplina',
                'icone': 'fa-fire',
                'cor': '#FF6B6B'
            },
            {
                'categoria': 'conhecimento',
                'nome': 'Conhecimento Financeiro',
                'icone': 'fa-graduation-cap',
                'cor': '#00BCD4'
            },
        ]
        
        for tipo_data in tipos:
            TipoConquista.objects.get_or_create(
                categoria=tipo_data['categoria'],
                defaults=tipo_data
            )

    def criar_conquistas(self):
        conquistas = [
            # DISCIPLINA
            {
                'tipo__categoria': 'disciplina',
                'titulo': 'Primeiro Passo',
                'descricao': 'Registrou sua primeira transação no Nebue',
                'raridade': 'comum',
                'pontos': 10,
                'icone': 'fa-shoe-prints',
                'condicao': 'Primeira transação',
                'meta_quantidade': 1
            },
            {
                'tipo__categoria': 'disciplina',
                'titulo': 'Primeira Semana Completa',
                'descricao': 'Manteve o registro por 7 dias consecutivos',
                'raridade': 'rara',
                'pontos': 50,
                'icone': 'fa-calendar-week',
                'condicao': '7 dias de streak',
                'meta_dias_consecutivos': 7
            },
            {
                'tipo__categoria': 'disciplina',
                'titulo': 'Um Mês de Controle',
                'descricao': 'Registrou transações por 30 dias seguidos',
                'raridade': 'epica',
                'pontos': 150,
                'icone': 'fa-calendar-alt',
                'condicao': '30 dias de streak',
                'meta_dias_consecutivos': 30
            },
            {
                'tipo__categoria': 'disciplina',
                'titulo': 'Trimestre Disciplinado',
                'descricao': 'Manteve o controle por 90 dias consecutivos',
                'raridade': 'epica',
                'pontos': 300,
                'icone': 'fa-medal',
                'condicao': '90 dias de streak',
                'meta_dias_consecutivos': 90
            },
            {
                'tipo__categoria': 'disciplina',
                'titulo': 'Ano de Ouro',
                'descricao': 'Um ano inteiro de disciplina financeira!',
                'raridade': 'lendaria',
                'pontos': 1000,
                'icone': 'fa-trophy',
                'condicao': '365 dias de streak',
                'meta_dias_consecutivos': 365
            },
            
            # ECONOMIA
            {
                'tipo__categoria': 'economia',
                'titulo': 'Primeira Reserva',
                'descricao': 'Alcançou R$ 500 em reserva de emergência',
                'raridade': 'comum',
                'pontos': 75,
                'icone': 'fa-coins',
                'condicao': 'R$ 500 em reserva',
                'meta_valor': 500
            },
            {
                'tipo__categoria': 'economia',
                'titulo': 'Mil Guardados',
                'descricao': 'Sua reserva chegou a R$ 1.000!',
                'raridade': 'rara',
                'pontos': 150,
                'icone': 'fa-sack-dollar',
                'condicao': 'R$ 1.000 em reserva',
                'meta_valor': 1000
            },
            {
                'tipo__categoria': 'economia',
                'titulo': 'Reserva Sólida',
                'descricao': 'Parabéns! R$ 5.000 de reserva',
                'raridade': 'epica',
                'pontos': 300,
                'icone': 'fa-vault',
                'condicao': 'R$ 5.000 em reserva',
                'meta_valor': 5000
            },
            {
                'tipo__categoria': 'economia',
                'titulo': 'Reserva de Elite',
                'descricao': 'Incrível! R$ 10.000 guardados',
                'raridade': 'lendaria',
                'pontos': 500,
                'icone': 'fa-gem',
                'condicao': 'R$ 10.000 em reserva',
                'meta_valor': 10000
            },
            
            # RECEITAS
            {
                'tipo__categoria': 'economia',
                'titulo': 'Primeiros Mil',
                'descricao': 'Registrou R$ 1.000 em receitas',
                'raridade': 'comum',
                'pontos': 50,
                'icone': 'fa-money-bill-wave',
                'condicao': 'R$ 1.000 em receitas',
                'meta_valor': 1000
            },
            {
                'tipo__categoria': 'economia',
                'titulo': 'Cinco Mil Acumulados',
                'descricao': 'Total de R$ 5.000 em receitas!',
                'raridade': 'rara',
                'pontos': 100,
                'icone': 'fa-money-bill-trend-up',
                'condicao': 'R$ 5.000 em receitas',
                'meta_valor': 5000
            },
            {
                'tipo__categoria': 'economia',
                'titulo': 'Dez Mil em Receitas',
                'descricao': 'Você registrou R$ 10.000 em receitas',
                'raridade': 'epica',
                'pontos': 200,
                'icone': 'fa-hand-holding-dollar',
                'condicao': 'R$ 10.000 em receitas',
                'meta_valor': 10000
            },
            {
                'tipo__categoria': 'economia',
                'titulo': 'Cinquenta Mil!',
                'descricao': 'Impressionante! R$ 50.000 em receitas',
                'raridade': 'lendaria',
                'pontos': 500,
                'icone': 'fa-sack-dollar',
                'condicao': 'R$ 50.000 em receitas',
                'meta_valor': 50000
            },
            
            # METAS
            {
                'tipo__categoria': 'organizacao',
                'titulo': 'Primeira Meta Alcançada',
                'descricao': 'Completou sua primeira meta financeira',
                'raridade': 'rara',
                'pontos': 100,
                'icone': 'fa-bullseye',
                'condicao': 'Completar 1 meta',
                'meta_quantidade': 1
            },
            {
                'tipo__categoria': 'organizacao',
                'titulo': 'Conquistador de Metas',
                'descricao': 'Completou 5 metas financeiras',
                'raridade': 'epica',
                'pontos': 250,
                'icone': 'fa-trophy',
                'condicao': 'Completar 5 metas',
                'meta_quantidade': 5
            },
            {
                'tipo__categoria': 'organizacao',
                'titulo': 'Mestre das Metas',
                'descricao': 'Incrível! 10 metas completadas',
                'raridade': 'lendaria',
                'pontos': 500,
                'icone': 'fa-crown',
                'condicao': 'Completar 10 metas',
                'meta_quantidade': 10
            },
            
            # QUITAÇÃO DE DÍVIDAS
            {
                'tipo__categoria': 'quitacao',
                'titulo': 'Primeira Dívida Quitada',
                'descricao': 'Parabéns por quitar sua primeira dívida!',
                'raridade': 'rara',
                'pontos': 150,
                'icone': 'fa-check-circle',
                'condicao': 'Quitar 1 dívida',
                'meta_quantidade': 1
            },
            {
                'tipo__categoria': 'quitacao',
                'titulo': 'Livre de Dívidas',
                'descricao': 'Você quitou todas as suas dívidas!',
                'raridade': 'lendaria',
                'pontos': 750,
                'icone': 'fa-hands-holding',
                'condicao': 'Quitar todas as dívidas',
                'meta_quantidade': 0
            },
            
            # CONHECIMENTO
            {
                'tipo__categoria': 'conhecimento',
                'titulo': 'Estudante Financeiro',
                'descricao': 'Leu 5 conteúdos educacionais',
                'raridade': 'comum',
                'pontos': 50,
                'icone': 'fa-book-open',
                'condicao': 'Ler 5 conteúdos',
                'meta_quantidade': 5
            },
            {
                'tipo__categoria': 'conhecimento',
                'titulo': 'Conhecedor das Finanças',
                'descricao': 'Completou 10 conteúdos educacionais',
                'raridade': 'rara',
                'pontos': 100,
                'icone': 'fa-graduation-cap',
                'condicao': 'Ler 10 conteúdos',
                'meta_quantidade': 10
            },
            
            # INVESTIMENTOS
            {
                'tipo__categoria': 'investimento',
                'titulo': 'Primeiro Investimento',
                'descricao': 'Registrou seu primeiro investimento',
                'raridade': 'rara',
                'pontos': 200,
                'icone': 'fa-seedling',
                'condicao': 'Primeiro investimento',
                'meta_quantidade': 1
            },
            {
                'tipo__categoria': 'investimento',
                'titulo': 'Carteira Diversificada',
                'descricao': 'Possui investimentos em 3 categorias diferentes',
                'raridade': 'epica',
                'pontos': 300,
                'icone': 'fa-chart-pie',
                'condicao': '3 tipos de investimento',
                'meta_quantidade': 3
            },
        ]
        
        for conquista_data in conquistas:
            tipo_categoria = conquista_data.pop('tipo__categoria')
            tipo = TipoConquista.objects.get(categoria=tipo_categoria)
            
            Conquista.objects.get_or_create(
                tipo=tipo,
                titulo=conquista_data['titulo'],
                defaults=conquista_data
            )