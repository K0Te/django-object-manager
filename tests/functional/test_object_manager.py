import os
import django
from django.test import TestCase

from django_object_manager.object_manager import ObjManagerMixin

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'  # noqa
django.setup()  # noqa

from tests.app import models, tests


class TestPlaneMake(ObjManagerMixin, TestCase):
    """Ensure that Object Manager can create objects."""

    def test_multiple_predefined(self):
        """Ensure that multiple predefined objects can be created."""
        users = self.object_manager.get_users()
        self.assertEqual(users['bob'].name, 'Bob')
        self.assertEqual(models.User.objects.count(), 2)

    def test_single_predefined(self):
        """Ensure that single object can be created by id."""
        bob = self.object_manager.get_user('bob')
        self.assertEqual(bob.name, 'Bob')
        self.assertEqual(models.User.objects.count(), 1)

    def test_double_get(self):
        """Ensure that single object is returned on two calls."""
        user1 = self.object_manager.get_user('bob')
        user2 = self.object_manager.get_user('bob')
        self.assertEqual(user1, user2)
        self.assertEqual(models.User.objects.count(), 1)

    def test_single_from_kwargs(self):
        """Ensure that single object can be created from params."""
        user3 = self.object_manager.get_user(name='Jack',
                                             email='test@test.org')
        self.assertEqual(user3.name, 'Jack')
        self.assertEqual(user3.email, 'test@test.org')
        self.assertEqual(models.User.objects.count(), 1)

    def test_foreign_key_predefined(self):
        """Ensure that single object FK can be specified using id."""
        film = self.object_manager.get_film(name='Memento',
                                            year=2000,
                                            uploaded_by='bob')
        self.assertEqual(film.uploaded_by.name, 'Bob')
        self.assertEqual(film.uploaded_by.email, 'bob@domain.com')
        self.assertEqual(models.User.objects.count(), 1)

    def test_foreing_key_as_instance(self):
        """Ensure that single object FK can be specified using instance."""
        user3 = self.object_manager.get_user(name='Jack',
                                             email='test@test.org')
        film = self.object_manager.get_film(name='Memento',
                                            year=2000,
                                            uploaded_by=user3)
        self.assertEqual(film.uploaded_by.name, 'Jack')
        self.assertEqual(film.uploaded_by.email, 'test@test.org')
        self.assertEqual(models.User.objects.count(), 1)

    def test_many_to_many_reversed_predefined(self):
        """Ensure that object with M2M relation can be created."""
        film1 = self.object_manager.get_film(name='Memento',
                                             year=2000,
                                             uploaded_by='bob')
        film2 = self.object_manager.get_film(name='The Godfather',
                                             year=1974,
                                             uploaded_by='bob')
        self.object_manager.get_filmcategory('crime',
                                             films=[film1, film2])
        self.assertEqual(models.FilmCategory.objects.count(), 1)

    # def test_many_to_many_forward_predefined(self):
    #     """Ensure that object with M2M relation can be created."""
    #     film = self.object_manager.get_film(name='Memento',
    #                                         year=2000,
    #                                         uploaded_by='bob',
    #                                         categories=['crime', 'drama'])
    #     self.assertEqual(models.FilmCategory.objects.count(), 2)
    #
    # def test_customized(self):
    #     """Ensure that customized objects are not cached."""
