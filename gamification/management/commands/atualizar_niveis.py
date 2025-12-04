# gamification/management/commands/atualizar_niveis.py
from django.core.management.base import BaseCommand
from gamification.models import NivelFinanceiro, TipoConquista, Conquista


class Command(BaseCommand):
    help = 'Atualiza níveis e adiciona mais conquistas'

    def handle(self, *args, **kwargs):
        self.stdout.write('Atualizando níveis financeiros...')
        self.atualizar_niveis()
        
        self.stdout.write('Adicionando novas conquistas...')
        self.adicionar_conquistas()
        
        self.stdout.write(self.style.SUCCESS('✅ Sistema atualizado com sucesso!'))

    def atualizar_niveis(self):
        # Deleta níveis antigos
        NivelFinanceiro.objects.all().delete()
        
        niveis = [
            {
                'numero': 1,
                'nome': 'Iniciante',
                'descricao': 'Começando a jornada financeira',
                'pontos_necessarios': 0,
                'icone': 'fa-seedling',
                'cor': '#6B7280'
            },
            {
                'numero': 2,
                'nome': 'Aprendiz',
                'descricao': 'Aprendendo o básico',
                'pontos_necessarios': 100,
                'icone': 'fa-book',
                'cor': '#8B5CF6'
            },
            {
                'numero': 3,
                'nome': 'Organizador',
                'descricao': 'Organizando as finanças',
                'pontos_necessarios': 300,
                'icone': 'fa-clipboard-check',
                'cor': '#A855F7'
            },
            {
                'numero': 4,
                'nome': 'Disciplinado',
                'descricao': 'Mantendo a disciplina',
                'pontos_necessarios': 600,
                'icone': 'fa-medal',
                'cor': '#C084FC'
            },
            {
                'numero': 5,
                'nome': 'Poupador',
                'descricao': 'Economizando com sabedoria',
                'pontos_necessarios': 1000,
                'icone': 'fa-piggy-bank',
                'cor': '#D8B4FE'
            },
            {
                'numero': 6,
                'nome': 'Estrategista',
                'descricao': 'Planejando o futuro',
                'pontos_necessarios': 1600,
                'icone': 'fa-chess',
                'cor': '#E9D5FF'
            },
            {
                'numero': 7,
                'nome': 'Investidor',
                'descricao': 'Fazendo o dinheiro trabalhar',
                'pontos_necessarios': 2500,
                'icone': 'fa-chart-line',
                'cor': '#F3E8FF'
            },
            {
                'numero': 8,
                'nome': 'Expert',
                'descricao': 'Dominando as finanças',
                'pontos_necessarios': 4000,
                'icone': 'fa-star',
                'cor': '#FAF5FF'
            },
            {
                'numero': 9,
                'nome': 'Mestre Financeiro',
                'descricao': 'Excelência absoluta conquistada!',
                'pontos_necessarios': 6500,
                'icone': 'fa-crown',
                'cor': '#FBBF24'
            },
        ]
        
        for nivel_data in niveis:
            NivelFinanceiro.objects.create(**nivel_data)
            self.stdout.write(f"  ✓ {nivel_data['nome']}")

    def adicionar_conquistas(self):
        # Adiciona conquistas intermediárias
        tipo_disciplina = TipoConquista.objects.get(categoria='disciplina')
        tipo_economia = TipoConquista.objects.get(categoria='economia')
        
        novas_conquistas = [
            {
                'tipo': tipo_disciplina,
                'titulo': '3 Dias Seguidos',
                'descricao': 'Manteve registro por 3 dias',
                'raridade': 'comum',
                'pontos': 15,
                'icone': 'fa-fire',
                'condicao': '3 dias de streak',
                'meta_dias_consecutivos': 3
            },
            {
                'tipo': tipo_disciplina,
                'titulo': 'Quinzena Consistente',
                'descricao': 'Registrou por 15 dias seguidos',
                'raridade': 'rara',
                'pontos': 75,
                'icone': 'fa-calendar',
                'condicao': '15 dias de streak',
                'meta_dias_consecutivos': 15
            },
            {
                'tipo': tipo_economia,
                'titulo': 'Primeira Economia',
                'descricao': 'Economizou R$ 100',
                'raridade': 'comum',
                'pontos': 25,
                'icone': 'fa-coins',
                'condicao': 'R$ 100 economizados',
                'meta_valor': 100
            },
            {
                'tipo': tipo_economia,
                'titulo': 'Economia Sólida',
                'descricao': 'Economizou R$ 2.000',
                'raridade': 'rara',
                'pontos': 100,
                'icone': 'fa-sack-dollar',
                'condicao': 'R$ 2.000 economizados',
                'meta_valor': 2000
            },
        ]
        
        for conquista_data in novas_conquistas:
            Conquista.objects.get_or_create(
                titulo=conquista_data['titulo'],
                defaults=conquista_data
            )