# django-object-manager
Simple, declarative, repeatable object management for Django tests

[![PyPI version](https://badge.fury.io/py/django-object-manager.svg)](https://badge.fury.io/py/django-object-manager)
[![Build Status](https://travis-ci.org/K0Te/django-object-manager.svg?branch=master)](https://travis-ci.org/K0Te/django-object-manager)
[![Coverage Status](https://coveralls.io/repos/github/K0Te/django-object-manager/badge.svg?branch=master)](https://coveralls.io/github/K0Te/django-object-manager?branch=master)

Examples:
```
# Model registration - usuallu in app/tests.py
# from .models import ...
from .models import User, Film, FilmCategory
from django_object_manager import ObjManagerMixin, ObjectManager


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
            'parent': 'serious',
        },
    })
ObjectManager.register(
    Film,
    {
        'memento': {
            'name': 'Memento',
            'year': 2000,
            'uploaded_by': 'bob',
            'categories': ['crime', 'drama']
        },
})

# Further usage in tests:
object_manager = ObjectManager() # or self.object_manager if inherited from 
# Single object creation - 'bob' is previously registered idenitifier
bob = object_manager.get_user('bob')

# Object creation with attribute owerwriting
user3 = object_manager.get_user('bob', email='other@domain.com')

# Fully custom object creation
user = object_manager.get_user(name='Jack',
                               email='test@test.org')
                                    
# All predefined objects of given model - returns id:object dictionary
user = object_manager.get_users()


# Object with dependencies - dependencies are referenced by
# - their registered indentifiers
# - by passing already created object

memento = object_manager.get_film('memento') # Will create two categories and one user
```
