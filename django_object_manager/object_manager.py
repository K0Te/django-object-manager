from collections import namedtuple, defaultdict
from datetime import datetime
from functools import partial

from django.db.models import (
    ForeignKey,
    ManyToManyRel,
    DateTimeField,
    OneToOneRel,
    ManyToManyField)
from pytz import utc


class ObjectManager:
    """Base class for test objects creation."""

    Context = namedtuple('Context', 'name many')
    _data = {}
    _registered_models = {}

    def __init__(self):
        """Initialize object creator."""
        self.context = None
        self._instances = defaultdict(dict)
        self._converters = {ForeignKey: self._create_foreing,
                            ManyToManyRel: self._create_m2m,
                            ManyToManyField: self._create_m2m,
                            DateTimeField: self._parse_datetime,
                            OneToOneRel: self._make1to1}

    @classmethod
    def register(cls, model, data):
        """Register model, which supports creation using data.keys()."""
        name = model.__name__.lower()
        cls._data[name] = data
        cls._registered_models[name] = model

    def __getattribute__(self, item):
        """Set context for object creation."""
        if not item.startswith('get_'):
            return super().__getattribute__(item)
        name = item.split('_', 1)[1]
        if name.endswith('s') and name[:-1] in self._registered_models:
            self.context = self.Context(name[:-1], True)
            return self
        elif name.endswith('ies') and \
                f'{name[:-3]}y' in self._registered_models:
            self.context = self.Context(f'{name[:-3]}y', True)
            return self
        elif name in self._registered_models:
            self.context = self.Context(name, False)
            return self
        else:
            raise RuntimeError(f'Unknown item: {item}, choices are: '
                               f'{self._registered_models.keys()}')

    def __call__(self, *args, **kwargs):
        """Create object(s)."""
        assert self.context is not None, 'x() instead of x.create_model()'
        if self.context.many and (args or kwargs):
            raise ValueError('Multiple item creation needs no args')
        name = self.context.name
        if self.context.many:
            return {key: self._get_or_create(name, key, **data)
                    for key, data in self._data[self.context.name].items()}
        else:
            try:
                (key,) = args
                item_data = self._data[self.context.name][key].copy()
                item_data.update(kwargs)
                params = item_data
            except ValueError:
                key = None
                params = kwargs
            return self._get_or_create(name, key,
                                       _custom=bool(kwargs),
                                       **params)

    def _get(self, _name, _key):
        if _key in self._instances[_name]:
            return self._instances[_name][_key]
        return None

    # TODO: Decrease complexity of the function
    def _create_dependencies(self, model, params): # noqa
        post_add = []
        for field in model._meta.get_fields():
            if field.name in params:
                if params[field.name] is None:
                    continue
                for (converter_type, converter) in self._converters.items():
                    if isinstance(field, converter_type):
                        params[field.name] = converter(field,
                                                       params[field.name])
                if isinstance(field, ManyToManyRel):
                    def cb(field, field_val, instance):
                        args = \
                            {instance._meta.model.__name__.lower(): instance,
                             field.related_model.__name__.lower(): field_val}
                        field.through(**args).save()
                    for related_val in params.pop(field.name):
                        post_add.append(partial(cb, field, related_val))
                elif isinstance(field, OneToOneRel):
                    def cb(field_val, instance):
                        setattr(field_val,
                                instance._meta.model.__name__.lower(),
                                instance)
                        field_val.save()
                    val = params.pop(field.name)
                    post_add.append(partial(cb, val))
        return post_add

    def _get_or_create(self, _name, _key, _create_in_db=True, _custom=False,
                       **kwargs):
        model = self._registered_models[_name]
        instance = self._get(_name, _key)
        if instance is not None and not _custom:
            return instance
        post_add = self._create_dependencies(model, kwargs)
        if _create_in_db:
            instance = model(**kwargs)
            instance.save(force_insert=True)
        else:
            return model(**kwargs)
        for action in post_add:
            action(instance)
        if _key is not None and not _custom:
            self._instances[_name][_key] = instance
        return instance

    def _create_foreing(self, field, value):
        foreing_model = field.rel.to
        name = foreing_model.__name__.lower()
        if isinstance(value, foreing_model):
            return value
        else:
            assert isinstance(value, str), \
                'Related values must be either instances or str ids'
            return self._get_or_create(name,
                                       value,
                                       **self._data[name][value])

    def _create_m2m(self, field, values):
        foreing_model = field.related_model
        name = foreing_model.__name__.lower()
        for value in values:
            if isinstance(value, foreing_model):
                yield value
            else:
                assert isinstance(value, str), \
                    'Related values must be either instances or str ids'
                yield self._get_or_create(name,
                                          value,
                                          **self._data[name][value])

    def _make1to1(self, field, value):
        foreing_model = field.related_model
        name = foreing_model.__name__.lower()
        assert isinstance(value, str)
        assert value not in self._instances[name]
        # DB record will be created during "main" model creation
        return self._get_or_create(name, value, _create_in_db=False,
                                   **self._data[name][value])

    def _parse_datetime(self, _field, value):
        return datetime.strptime(value, '%b %d %Y').replace(tzinfo=utc)


class ObjManagerMixin:
    """Mixin for easy test object creation."""

    object_manager = None

    def setUp(self):
        """Set test environment up."""
        self.object_manager = ObjectManager()
        super().setUp()
