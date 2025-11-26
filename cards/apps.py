from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'  # ← TEM QUE SER 'cards'
    verbose_name = 'Cartões de Crédito'