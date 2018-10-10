"""Field converters module, converter determines how field is created."""

from functools import partial
from collections import namedtuple

from django.db.models import (
    ForeignKey,
    ManyToManyRel,
    ManyToManyField,
    OneToOneRel,
)

__all__ = ('default_converters',)

FieldConverterResult = namedtuple('FieldConverterResult',
                                  'field_value post_actions pass_field_value')


def create_foreign_key(object_manager, field, value):
    foreign_model = field.remote_field.model
    name = foreign_model.__name__.lower()
    post_actions = []
    pass_field_value = True
    if isinstance(value, foreign_model):
        # FK value is already initialized, nothing to do here
        value = value
    else:
        assert isinstance(value, str), \
            'Related values must be either instances or str ids'
        # TODO Use type to select related model, name can be misleading !
        value = object_manager._get_or_create(
            name,
            value,
            **object_manager._data[name][value])
    return FieldConverterResult(value, post_actions, pass_field_value)


# TODO M2M are similar, probably they can be combined
def create_m2m_reverse(object_manager, field, values):

    def cb(field, field_val, instance):
        args = \
            {instance._meta.model.__name__.lower(): instance,
             field.related_model.__name__.lower(): field_val}
        # Create dependency after main object, using
        # M2M "through" model
        field.through(**args).save()

    foreing_model = field.related_model
    name = foreing_model.__name__.lower()

    def gen():
        for value in values:
            if isinstance(value, foreing_model):
                yield value
            else:
                assert isinstance(value, str), \
                    'Related values must be either instances or str ids'
                yield object_manager._get_or_create(name,
                                          value,
                                          **object_manager._data[name][value])
    res = list(gen())
    return FieldConverterResult(
        [],
        [partial(cb, field, related_val) for related_val in res],
        False)


def create_m2m_forward(object_manager, field, values):

    def cb(field, field_val, instance):
        field_val.save()
        # Delay forward M2M dependency,
        # use RelatedManager helper
        # TODO no related manager if `through` model has extra attributes ???
        getattr(instance, field.name).add(field_val)
    foreing_model = field.related_model
    name = foreing_model.__name__.lower()

    def gen():
        for value in values:
            if isinstance(value, foreing_model):
                yield value
            else:
                assert isinstance(value, str), \
                    'Related values must be either instances or str ids'
                yield object_manager._get_or_create(name,
                                                    value,
                                                    **object_manager._data[name][value])
    res = list(gen())
    return FieldConverterResult(
        [],
        [partial(cb, field, related_val) for related_val in res],
        False)


def create_one2one(object_manager, field, value):
    foreing_model = field.related_model
    name = foreing_model.__name__.lower()
    assert isinstance(value, str)
    assert value not in object_manager._instances[name]
    # DB record will be created during "main" model creation
    def cb(field_val, instance):
        setattr(field_val,
                instance._meta.model.__name__.lower(),
                instance)
        # Delay 1-to-1 dependency object creation
        field_val.save()
    value = object_manager._get_or_create(name, value, _create_in_db=False,
                                          **object_manager._data[name][value])
    return FieldConverterResult(
        value,
        [partial(cb, value)],
        True)


default_converters = {ForeignKey: create_foreign_key,
                      ManyToManyRel: create_m2m_reverse,
                      ManyToManyField: create_m2m_forward,
                      OneToOneRel: create_one2one,
                      }
