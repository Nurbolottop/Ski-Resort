from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_rename_baytur'),
    ]

    operations = [
        migrations.AddField(
            model_name='heroslide',
            name='image_alt',
            field=models.CharField(blank=True, help_text='Что на фото — для поисковиков и незрячих. Пусто — используется подзаголовок', max_length=255, verbose_name='Подпись к фото (alt)'),
        ),
    ]
