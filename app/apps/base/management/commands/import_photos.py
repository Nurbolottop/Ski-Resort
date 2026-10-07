"""
Загрузка фото в сайт из папки:

    <папка>/slides/*.jpg               → слайды главной (по порядку)
    <папка>/about.jpg                  → фото блока «О базе»
    <папка>/rooms/<slug>.jpg           → обложки жилья
    <папка>/services/<slug>.jpg        → обложки категорий услуг
    <папка>/gallery/<album-slug>/*.jpg → галерея по альбомам

    python manage.py import_photos /opt/ski/import
    python manage.py import_photos /opt/ski/import --replace   # заменить уже загруженную галерею

Файлы сохраняются через модели (ужимаются и переводятся в WEBP), как при загрузке из админки.
"""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.base.models import HeroSlide, SiteSettings
from apps.cms.models import GalleryAlbum, GalleryImage, Room, ServiceCategory

IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp'}


def images(folder):
    return sorted(p for p in Path(folder).glob('*') if p.suffix.lower() in IMAGE_EXT)


def attach(instance, field, path):
    with open(path, 'rb') as f:
        getattr(instance, field).save(path.name, File(f), save=True)


class Command(BaseCommand):
    help = 'Загружает фото из папки в слайды, галерею, жильё и блок «О базе».'

    def add_arguments(self, parser):
        parser.add_argument('folder')
        parser.add_argument('--replace', action='store_true', help='Удалить старые фото галереи перед загрузкой')

    @transaction.atomic
    def handle(self, folder, replace=False, **options):
        root = Path(folder)
        if not root.is_dir():
            raise CommandError(f'Нет папки {root}')

        slides = images(root / 'slides')
        for slide, path in zip(HeroSlide.objects.filter(is_active=True).order_by('order', 'pk'), slides):
            attach(slide, 'image', path)
        self.stdout.write(f'Слайды: {min(len(slides), HeroSlide.objects.count())}')

        about = next((p for p in root.glob('about.*') if p.suffix.lower() in IMAGE_EXT), None)
        if about:
            attach(SiteSettings.load(), 'about_image', about)
            self.stdout.write('Фото «О базе»: да')

        for path in images(root / 'rooms'):
            room = Room.objects.filter(slug=path.stem).first()
            if room:
                attach(room, 'cover', path)
                self.stdout.write(f'Жильё: {room.name}')

        for path in images(root / 'services'):
            category = ServiceCategory.objects.filter(slug=path.stem).first()
            if category:
                attach(category, 'cover', path)
                self.stdout.write(f'Услуги: {category.name}')

        gallery_root = root / 'gallery'
        if gallery_root.is_dir():
            for album_dir in sorted(p for p in gallery_root.iterdir() if p.is_dir()):
                album = GalleryAlbum.objects.filter(slug=album_dir.name).first()
                if not album:
                    self.stdout.write(self.style.WARNING(f'Нет альбома {album_dir.name}, пропускаю'))
                    continue
                if replace:
                    album.images.all().delete()
                elif album.images.exists():
                    self.stdout.write(f'Альбом «{album}» уже заполнен, пропускаю (--replace для замены)')
                    continue
                files = images(album_dir)
                for i, path in enumerate(files):
                    item = GalleryImage(album=album, order=i)
                    attach(item, 'image', path)
                self.stdout.write(f'Альбом «{album}»: {len(files)} фото')

        self.stdout.write(self.style.SUCCESS('Фото загружены.'))
