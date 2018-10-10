from django.db import models
from django.db.models import SET_NULL


class User(models.Model):
    id = models.AutoField('Identifier', primary_key=True)
    name = models.CharField('Name', max_length=70)
    email = models.EmailField()
    extra_info = models.OneToOneField('UserExtraInfo',
                                      null=True,
                                      on_delete=SET_NULL)


class UserExtraInfo(models.Model):
    address = models.CharField('Address', max_length=128)


class FilmCategory(models.Model):
    id = models.AutoField('Identifier', primary_key=True)
    name = models.CharField('Name', max_length=70)
    parent_category = models.ForeignKey('FilmCategory',
                                        null=True,
                                        default=None,
                                        on_delete=models.PROTECT)


# class FilmToFilmCategory(models.Model):
#     id = models.AutoField('Identifier', primary_key=True)
#     created = models.DateTimeField('Created', auto_now_add=True)


class Film(models.Model):
    id = models.AutoField('Identifier', primary_key=True)
    year = models.IntegerField('Year')
    name = models.CharField('Name', max_length=70)
    uploaded_by = models.ForeignKey(User,
                                    related_name='uploaded_films',
                                    on_delete=models.PROTECT)
    categories = models.ManyToManyField(FilmCategory,
                                        related_name='films',
                                        # through=FilmToFilmCategory
                                        )
