"""
Management command para popular o sistema de gamificação
Execute: python manage.py popular_gamificacao
"""
from django.core.management.base import BaseCommand
from gamification.models import NivelFinanceiro, Conquista, TipoConquista


class Command(BaseCommand):
    help = 'Popula o sistema de gamificação com níveis e conquistas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎮 Iniciando população do sistema de gamificação...'))
        
        self.popular_niveis()
        self.popular_tipos_conquista()
        self.popular_conquistas()
        
        self.stdout.write(self.style.SUCCESS('✅ Sistema de gamificação populado com sucesso!'))
    
    def popular_niveis(self):
        """Cria os níveis do sistema"""
        self.stdout.write('📊 Criando níveis...')
        
        niveis = [
            {
                'numero': 1,
                'nome': 'Iniciante',
                'descricao': 'Começando sua jornada rumo à estabilidade financeira',
                'pontos_necessarios': 0,
                'icone': 'fa-seedling',  # 🌱
                'cor': '#10b981'
            },
            {
                'numero': 2,
                'nome': 'Aprendiz',
                'descricao': 'Aprendendo o básico sobre finanças',
                'pontos_necessarios': 100,
                'icone': 'fa-book-open',  # 📖
                'cor': '#3b82f6'
            },
            {
                'numero': 3,
                'nome': 'Organizador',
                'descricao': 'Organizando as finanças',
                'pontos_necessarios': 300,
                'icone': 'fa-clipboard-list',  # 📋
                'cor': '#8b5cf6'
            },
            {
                'numero': 4,
                'nome': 'Disciplinado',
                'descricao': 'Mantendo a disciplina',
                'pontos_necessarios': 600,
                'icone': 'fa-chart-line',  # 📈
                'cor': '#06b6d4'
            },
            {
                'numero': 5,
                'nome': 'Poupador',
                'descricao': 'Economizando com inteligência',
                'pontos_necessarios': 1000,
                'icone': 'fa-piggy-bank',  # 🐷
                'cor': '#ec4899'
            },
            {
                'numero': 6,
                'nome': 'Equilibrado',
                'descricao': 'Mantendo o equilíbrio financeiro',
                'pontos_necessarios': 1500,
                'icone': 'fa-balance-scale',  # ⚖️
                'cor': '#14b8a6'
            },
            {
                'numero': 7,
                'nome': 'Campeão',
                'descricao': 'Conquistando suas metas financeiras',
                'pontos_necessarios': 2500,
                'icone': 'fa-trophy',  # 🏆
                'cor': '#f59e0b'
            },
            {
                'numero': 8,
                'nome': 'Expert',
                'descricao': 'Expert em gestão financeira',
                'pontos_necessarios': 4000,
                'icone': 'fa-graduation-cap',  # 🎓
                'cor': '#a855f7'
            },
            {
                'numero': 9,
                'nome': 'Guardião',
                'descricao': 'Guardião das suas finanças',
                'pontos_necessarios': 6000,
                'icone': 'fa-shield-alt',  # 🛡️
                'cor': '#ef4444'
            },
            {
                'numero': 10,
                'nome': 'Mestre',
                'descricao': 'Mestre das finanças pessoais',
                'pontos_necessarios': 10000,
                'icone': 'fa-crown',  # 👑
                'cor': '#fbbf24'
            }
        ]
        
        for nivel_data in niveis:
            nivel, created = NivelFinanceiro.objects.update_or_create(
                numero=nivel_data['numero'],
                defaults=nivel_data
            )
            if created:
                self.stdout.write(f'  ✓ Nível {nivel.numero} - {nivel.nome} criado')
            else:
                self.stdout.write(f'  ✓ Nível {nivel.numero} - {nivel.nome} atualizado')
    
    def popular_tipos_conquista(self):
        """Cria os tipos de conquista"""
        self.stdout.write('🏷️  Criando tipos de conquista...')
        
        tipos = [
            {'nome': 'Transações', 'categoria': 'transacoes', 'icone': 'fa-exchange-alt', 'cor': '#3b82f6'},
            {'nome': 'Orçamentos', 'categoria': 'orcamentos', 'icone': 'fa-calculator', 'cor': '#10b981'},
            {'nome': 'Cartões', 'categoria': 'cartoes', 'icone': 'fa-credit-card', 'cor': '#8b5cf6'},
            {'nome': 'Categorias', 'categoria': 'categorias', 'icone': 'fa-tags', 'cor': '#f59e0b'},
            {'nome': 'Economia', 'categoria': 'economia', 'icone': 'fa-piggy-bank', 'cor': '#22c55e'},
            {'nome': 'Streak', 'categoria': 'streak', 'icone': 'fa-fire', 'cor': '#ef4444'},
            {'nome': 'Geral', 'categoria': 'geral', 'icone': 'fa-trophy', 'cor': '#fbbf24'},
        ]
        
        for tipo_data in tipos:
            tipo, created = TipoConquista.objects.get_or_create(
                categoria=tipo_data['categoria'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f'  ✓ Tipo {tipo.nome} criado')
    
    def popular_conquistas(self):
        """Cria as conquistas do sistema"""
        self.stdout.write('🏆 Criando conquistas...')
        
        conquistas = [
            # Conquistas de Boas-Vindas
            {
                'codigo': 'bem_vindo',
                'titulo': 'Bem-vindo ao Nebue!',
                'descricao': 'Complete seu cadastro e comece sua jornada',
                'condicao': 'Criar conta no sistema',
                'icone': 'fa-hand-wave',
                'pontos': 50,
                'raridade': 'comum',
                'tipo_categoria': 'geral'
            },
            
            # Conquistas de Transações
            {
                'codigo': 'primeira_transacao',
                'titulo': 'Primeira Transação',
                'descricao': 'Registre sua primeira transação no sistema',
                'condicao': 'Criar 1 transação',
                'icone': 'fa-receipt',
                'pontos': 100,
                'raridade': 'comum',
                'tipo_categoria': 'transacoes',
                'meta_quantidade': 1
            },
            {
                'codigo': '10_transacoes',
                'titulo': 'Organizador Iniciante',
                'descricao': 'Registre 10 transações',
                'condicao': 'Criar 10 transações',
                'icone': 'fa-list-check',
                'pontos': 200,
                'raridade': 'comum',
                'tipo_categoria': 'transacoes',
                'meta_quantidade': 10
            },
            {
                'codigo': '50_transacoes',
                'titulo': 'Controlador Financeiro',
                'descricao': 'Registre 50 transações',
                'condicao': 'Criar 50 transações',
                'icone': 'fa-clipboard-check',
                'pontos': 500,
                'raridade': 'rara',
                'tipo_categoria': 'transacoes',
                'meta_quantidade': 50
            },
            {
                'codigo': '100_transacoes',
                'titulo': 'Mestre do Controle',
                'descricao': 'Registre 100 transações',
                'condicao': 'Criar 100 transações',
                'icone': 'fa-chart-pie',
                'pontos': 1000,
                'raridade': 'epica',
                'tipo_categoria': 'transacoes',
                'meta_quantidade': 100
            },
            
            # Conquistas de Orçamentos
            {
                'codigo': 'primeiro_orcamento',
                'titulo': 'Primeiro Orçamento',
                'descricao': 'Crie seu primeiro orçamento mensal',
                'condicao': 'Criar 1 orçamento',
                'icone': 'fa-calculator',
                'pontos': 150,
                'raridade': 'comum',
                'tipo_categoria': 'orcamentos',
                'meta_quantidade': 1
            },
            
            # Conquistas de Cartões
            {
                'codigo': 'primeiro_cartao',
                'titulo': 'Primeiro Cartão',
                'descricao': 'Cadastre seu primeiro cartão de crédito',
                'condicao': 'Cadastrar 1 cartão',
                'icone': 'fa-credit-card',
                'pontos': 100,
                'raridade': 'comum',
                'tipo_categoria': 'cartoes',
                'meta_quantidade': 1
            },
            
            # Conquistas de Categorias
            {
                'codigo': 'organizador_expert',
                'titulo': 'Organizador Expert',
                'descricao': 'Crie 10 categorias personalizadas',
                'condicao': 'Criar 10 categorias',
                'icone': 'fa-tags',
                'pontos': 300,
                'raridade': 'rara',
                'tipo_categoria': 'categorias',
                'meta_quantidade': 10
            },
            
            # Conquistas de Streak
            {
                'codigo': 'streak_7',
                'titulo': 'Uma Semana Ativo',
                'descricao': 'Mantenha uma sequência de 7 dias',
                'condicao': '7 dias consecutivos',
                'icone': 'fa-fire',
                'pontos': 200,
                'raridade': 'rara',
                'tipo_categoria': 'streak',
                'meta_dias_consecutivos': 7
            },
            {
                'codigo': 'streak_30',
                'titulo': 'Hábito Mensal',
                'descricao': 'Mantenha uma sequência de 30 dias',
                'condicao': '30 dias consecutivos',
                'icone': 'fa-fire-flame-curved',
                'pontos': 800,
                'raridade': 'epica',
                'tipo_categoria': 'streak',
                'meta_dias_consecutivos': 30
            },
            {
                'codigo': 'streak_100',
                'titulo': 'Disciplina de Ferro',
                'descricao': 'Mantenha uma sequência de 100 dias',
                'condicao': '100 dias consecutivos',
                'icone': 'fa-fire-flame-simple',
                'pontos': 2000,
                'raridade': 'lendaria',
                'tipo_categoria': 'streak',
                'meta_dias_consecutivos': 100
            },
            
            # Conquistas Especiais
            {
                'codigo': 'madrugador',
                'titulo': 'Madrugador',
                'descricao': 'Registre uma transação antes das 6h da manhã',
                'condicao': 'Transação antes das 6h',
                'icone': 'fa-mug-hot',
                'pontos': 50,
                'raridade': 'comum',
                'tipo_categoria': 'geral'
            },
            {
                'codigo': 'nivel_5',
                'titulo': 'Mestre Alcançado',
                'descricao': 'Alcance o nível 5',
                'condicao': 'Chegar ao nível 5',
                'icone': 'fa-star',
                'pontos': 500,
                'raridade': 'epica',
                'tipo_categoria': 'geral'
            },
        ]
        
        for conquista_data in conquistas:
            tipo_categoria = conquista_data.pop('tipo_categoria')
            tipo = TipoConquista.objects.get(categoria=tipo_categoria)
            
            conquista, created = Conquista.objects.get_or_create(
                codigo=conquista_data['codigo'],
                defaults={**conquista_data, 'tipo': tipo}
            )
            
            if created:
                self.stdout.write(f'  ✓ Conquista "{conquista.titulo}" criada')
            else:
                self.stdout.write(f'  - Conquista "{conquista.titulo}" já existe')