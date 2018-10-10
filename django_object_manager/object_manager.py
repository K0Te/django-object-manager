from collections import namedtuple, defaultdict
from functools import partial

from django.db.models import (
    ForeignKey,
    ManyToManyRel,
    OneToOneRel,
    ManyToManyField)


class ContextCallable:
    """Callable helper used for context passing to ObjectManager."""

    def __init__(self, object_manager, context):
        """Initialize context callable."""
        self.context = context
        self.object_manager = object_manager

    def __call__(self, *args, **kwargs):
        """Create object(s)."""
        return self.object_manager.call_with_context(self.context,
                                                     *args,
                                                     **kwargs)


class ObjectManager:
    """Base class for test objects creation."""

    Context = namedtuple('Context', 'name many')
    _data = {}
    _registered_models = {}

    def __init__(self):
        """Initialize object creator."""
        self._instances = defaultdict(dict)
        self._converters = {ForeignKey: self._create_foreing,
                            ManyToManyRel: self._create_m2m_rel,
                            ManyToManyField: self._create_m2m_field,
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
            return self.with_context(self.Context(name=name[:-1], many=True))
        elif name.endswith('ies') and \
                f'{name[:-3]}y' in self._registered_models:
            return self.with_context(self.Context(name=f'{name[:-3]}y', many=True))
        elif name in self._registered_models:
            return self.with_context(self.Context(name=name, many=False))
        else:
            raise RuntimeError(f'Unknown item: {item}, choices are: '
                               f'{self._registered_models.keys()}')

    def with_context(self, context):
        return ContextCallable(self, context)

    def __call__(self, *args, **kwargs):
        """Implemented to provide better error message."""
        raise RuntimeError(
            'object_manager() instead of object_manager.get_`model_name`()')

    def call_with_context(self, context, *args, **kwargs):
        if context.many and (args or kwargs):
            raise ValueError('Multiple item creation needs no args')
        if context.many:
            return {key: self._get_or_create(context.name, key, **data)
                    for key, data in self._data[context.name].items()}
        else:
            try:
                (key,) = args
                item_data = self._data[context.name][key].copy()
                item_data.update(kwargs)
                params = item_data
            except ValueError:
                key = None
                params = kwargs
            return self._get_or_create(context.name, key,
                                       _custom=bool(kwargs),
                                       **params)

    def _get(self, _name, _key):
        if _key in self._instances[_name]:
            return self._instances[_name][_key]
        return None

    def _create_dependencies(self, model, params):
        cbs = []
        for field in model._meta.get_fields():
            if field.name in params:
                if params[field.name] is None:
                    continue
                for (converter_type, converter) in self._converters.items():
                    if isinstance(field, converter_type):
                        # TODO use namedtuple here ?
                        params[field.name], new_cbs, pop_params = converter(field,
                                                       params[field.name])
                        cbs.extend(new_cbs)
                        if pop_params:
                            params.pop(field.name)

        return cbs

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
        foreing_model = field.remote_field.model
        name = foreing_model.__name__.lower()
        if isinstance(value, foreing_model):
            return value, [], False
        else:
            assert isinstance(value, str), \
                'Related values must be either instances or str ids'
            # TODO Use type to select related model, name can be misleading !
            return self._get_or_create(name,
                                       value,
                                       **self._data[name][value]), [], False

    # TODO M2M are similar, probably they can be combined
    def _create_m2m_rel(self, field, values):
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
                    yield self._get_or_create(name,
                                              value,
                                              **self._data[name][value])
        return gen(), [partial(cb, field, related_val) for related_val in values], True

    def _create_m2m_field(self, field, values):
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
                    yield self._get_or_create(name,
                                              value,
                                              **self._data[name][value])
        res = list(gen())
        return res, [partial(cb, field, related_val) for related_val in res], True

    def _make1to1(self, field, value):
        foreing_model = field.related_model
        name = foreing_model.__name__.lower()
        assert isinstance(value, str)
        assert value not in self._instances[name]
        # DB record will be created during "main" model creation
        def cb(field_val, instance):
            setattr(field_val,
                    instance._meta.model.__name__.lower(),
                    instance)
            # Delay 1-to-1 dependency object creation
            field_val.save()
        return self._get_or_create(name, value, _create_in_db=False,
                                   **self._data[name][value]), [partial(cb, value)], [], False


class ObjManagerMixin:
    """Mixin for easy test object creation."""

    object_manager = None

    def setUp(self):
        """Set test environment up."""
        self.object_manager = ObjectManager()
        super().setUp()
