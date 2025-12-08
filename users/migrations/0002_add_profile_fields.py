# Generated migration for users app
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='nome_usuario',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='Nome de Usuário'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='nome_completo',
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name='Nome Completo'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='telefone',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Telefone'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='foto_perfil',
            field=models.ImageField(blank=True, null=True, upload_to='perfil/', verbose_name='Foto de Perfil'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='bio',
            field=models.TextField(blank=True, max_length=500, null=True, verbose_name='Biografia'),
        ),
    ]