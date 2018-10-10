"""Tests helpers for application."""

from django_object_manager.object_manager import ObjectManager
from .models import User, Film, FilmCategory, UserExtraInfo

ObjectManager.register(
    User,
    {
        'bob': {
            'name': 'Bob',
            'email': 'bob@domain.com',
        },
        'alice': {
            'name': 'Alice',
            'email': 'alice@example.com',
        },
    })
ObjectManager.register(
    FilmCategory,
    {
        'drama': {
            'name': 'Drama',
        },
        'crime': {
            'name': 'Crime',
        },
        'serious': {
            'name': 'Adult films',
        },
        'anime': {
            'name': 'Anime',
            'parent_category': 'serious',
        },
    })
ObjectManager.register(
    Film,
    {
    })
ObjectManager.register(
    UserExtraInfo,
    {
        'extra_info_1': {
            'address': 'NY'
        }
    })
