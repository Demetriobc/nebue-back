from django.core.management.base import BaseCommand
from gamification.models import Nivel, Conquista, TipoConquista


class Command(BaseCommand):
    help = 'Popula o sistema de gamificação com níveis e conquistas'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando população do sistema de gamificação...'))
        
        # Popular Níveis
        self.popular_niveis()
        
        # Popular Tipos de Conquista
        self.popular_tipos_conquista()
        
        # Popular Conquistas
        self.popular_conquistas()
        
        self.stdout.write(self.style.SUCCESS('✅ Sistema de gamificação populado com sucesso!'))
    
    def popular_niveis(self):
        """Cria os níveis do sistema"""
        self.stdout.write('Criando níveis...')
        
        niveis = [
            {
                'numero': 1,
                'nome': 'Iniciante',
                'descricao': 'Começando sua jornada rumo à estabilidade financeira',
                'pontos_necessarios': 0,
                'icone': 'fa-star',
                'cor': '#94a3b8'
            },
            {
                'numero': 2,
                'nome': 'Aprendiz',
                'descricao': 'Aprendendo a controlar suas finanças',
                'pontos_necessarios': 500,
                'icone': 'fa-seedling',
                'cor': '#84cc16'
            },
            {
                'numero': 3,
                'nome': 'Econômico',
                'descricao': 'Começando a economizar com inteligência',
                'pontos_necessarios': 1500,
                'icone': 'fa-piggy-bank',
                'cor': '#22c55e'
            },
            {
                'numero': 4,
                'nome': 'Investidor',
                'descricao': 'Fazendo seu dinheiro trabalhar para você',
                'pontos_necessarios': 3000,
                'icone': 'fa-chart-line',
                'cor': '#3b82f6'
            },
            {
                'numero': 5,
                'nome': 'Estrategista',
                'descricao': 'Planejando seu futuro financeiro com maestria',
                'pontos_necessarios': 5000,
                'icone': 'fa-chess',
                'cor': '#8b5cf6'
            },
            {
                'numero': 6,
                'nome': 'Expert',
                'descricao': 'Dominando o controle financeiro pessoal',
                'pontos_necessarios': 8000,
                'icone': 'fa-graduation-cap',
                'cor': '#a855f7'
            },
            {
                'numero': 7,
                'nome': 'Mestre',
                'descricao': 'Referência em gestão financeira',
                'pontos_necessarios': 12000,
                'icone': 'fa-crown',
                'cor': '#ec4899'
            },
            {
                'numero': 8,
                'nome': 'Lendário',
                'descricao': 'Entre os melhores investidores do Nebue',
                'pontos_necessarios': 20000,
                'icone': 'fa-trophy',
                'cor': '#fbbf24'
            }
        ]
        
        for nivel_data in niveis:
            nivel, created = Nivel.objects.get_or_create(
                numero=nivel_data['numero'],
                defaults=nivel_data
            )
            if created:
                self.stdout.write(f'  ✓ Nível {nivel.numero} - {nivel.nome} criado')
            else:
                self.stdout.write(f'  - Nível {nivel.numero} - {nivel.nome} já existe')
    
    def popular_tipos_conquista(self):
        """Cria os tipos de conquista"""
        self.stdout.write('Criando tipos de conquista...')
        
        tipos = [
            {'nome': 'Transações', 'categoria': 'transacoes'},
            {'nome': 'Metas', 'categoria': 'metas'},
            {'nome': 'Investimentos', 'categoria': 'investimentos'},
            {'nome': 'Economia', 'categoria': 'economia'},
            {'nome': 'Streak', 'categoria': 'streak'},
            {'nome': 'Geral', 'categoria': 'geral'},
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
        self.stdout.write('Criando conquistas...')
        
        conquistas = [
            # Conquistas de Boas-Vindas
            {
                'codigo': 'bem_vindo',
                'titulo': 'Bem-vindo ao Nebue!',
                'descricao': 'Complete seu cadastro e comece sua jornada',
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
                'icone': 'fa-receipt',
                'pontos': 100,
                'raridade': 'comum',
                'tipo_categoria': 'transacoes'
            },
            {
                'codigo': '10_transacoes',
                'titulo': 'Organizador Iniciante',
                'descricao': 'Registre 10 transações',
                'icone': 'fa-list-check',
                'pontos': 200,
                'raridade': 'comum',
                'tipo_categoria': 'transacoes'
            },
            {
                'codigo': '50_transacoes',
                'titulo': 'Controlador Financeiro',
                'descricao': 'Registre 50 transações',
                'icone': 'fa-clipboard-check',
                'pontos': 500,
                'raridade': 'rara',
                'tipo_categoria': 'transacoes'
            },
            {
                'codigo': '100_transacoes',
                'titulo': 'Mestre do Controle',
                'descricao': 'Registre 100 transações',
                'icone': 'fa-chart-pie',
                'pontos': 1000,
                'raridade': 'epica',
                'tipo_categoria': 'transacoes'
            },
            
            # Conquistas de Metas
            {
                'codigo': 'primeira_meta',
                'titulo': 'Primeira Meta',
                'descricao': 'Crie sua primeira meta de economia',
                'icone': 'fa-bullseye',
                'pontos': 100,
                'raridade': 'comum',
                'tipo_categoria': 'metas'
            },
            {
                'codigo': 'meta_concluida',
                'titulo': 'Objetivo Alcançado',
                'descricao': 'Complete sua primeira meta',
                'icone': 'fa-flag-checkered',
                'pontos': 300,
                'raridade': 'rara',
                'tipo_categoria': 'metas'
            },
            {
                'codigo': '5_metas',
                'titulo': 'Planejador Expert',
                'descricao': 'Complete 5 metas diferentes',
                'icone': 'fa-trophy',
                'pontos': 800,
                'raridade': 'epica',
                'tipo_categoria': 'metas'
            },
            
            # Conquistas de Streak
            {
                'codigo': 'streak_7',
                'titulo': 'Uma Semana Ativo',
                'descricao': 'Mantenha uma sequência de 7 dias',
                'icone': 'fa-fire',
                'pontos': 200,
                'raridade': 'rara',
                'tipo_categoria': 'streak'
            },
            {
                'codigo': 'streak_30',
                'titulo': 'Hábito Mensal',
                'descricao': 'Mantenha uma sequência de 30 dias',
                'icone': 'fa-fire-flame-curved',
                'pontos': 800,
                'raridade': 'epica',
                'tipo_categoria': 'streak'
            },
            {
                'codigo': 'streak_100',
                'titulo': 'Disciplina de Ferro',
                'descricao': 'Mantenha uma sequência de 100 dias',
                'icone': 'fa-fire-flame-simple',
                'pontos': 2000,
                'raridade': 'lendaria',
                'tipo_categoria': 'streak'
            },
            
            # Conquistas de Investimentos
            {
                'codigo': 'primeiro_investimento',
                'titulo': 'Primeiro Investimento',
                'descricao': 'Registre seu primeiro investimento',
                'icone': 'fa-chart-line',
                'pontos': 300,
                'raridade': 'rara',
                'tipo_categoria': 'investimentos'
            },
            {
                'codigo': 'investidor_diversificado',
                'titulo': 'Investidor Diversificado',
                'descricao': 'Tenha investimentos em 3 categorias diferentes',
                'icone': 'fa-layer-group',
                'pontos': 800,
                'raridade': 'epica',
                'tipo_categoria': 'investimentos'
            },
            
            # Conquistas de Economia
            {
                'codigo': 'economizador',
                'titulo': 'Primeiro Economizador',
                'descricao': 'Tenha mais receitas que despesas em um mês',
                'icone': 'fa-piggy-bank',
                'pontos': 250,
                'raridade': 'comum',
                'tipo_categoria': 'economia'
            },
            {
                'codigo': 'poupador',
                'titulo': 'Poupador Consistente',
                'descricao': 'Economize por 3 meses seguidos',
                'icone': 'fa-sack-dollar',
                'pontos': 600,
                'raridade': 'rara',
                'tipo_categoria': 'economia'
            },
            
            # Conquistas Especiais
            {
                'codigo': 'madrugador',
                'titulo': 'Madrugador',
                'descricao': 'Registre uma transação antes das 6h da manhã',
                'icone': 'fa-mug-hot',
                'pontos': 50,
                'raridade': 'comum',
                'tipo_categoria': 'geral'
            },
            {
                'codigo': 'nivel_5',
                'titulo': 'Estrategista Alcançado',
                'descricao': 'Alcance o nível 5',
                'icone': 'fa-star',
                'pontos': 500,
                'raridade': 'epica',
                'tipo_categoria': 'geral'
            },
            {
                'codigo': 'nivel_8',
                'titulo': 'Lenda do Nebue',
                'descricao': 'Alcance o nível máximo',
                'icone': 'fa-crown',
                'pontos': 2000,
                'raridade': 'lendaria',
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