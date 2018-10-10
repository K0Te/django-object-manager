from collections import namedtuple, defaultdict
from copy import copy

from .field_converters import default_converters


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
        self._converters = copy(default_converters)

    @classmethod
    def register(cls, model, data):
        """Register model, which supports creation using data.keys()."""
        name = model.__name__.lower()
        cls._data[name] = data
        cls._registered_models[name] = model

    @classmethod
    def register_converter(cls, field_type, converter):
        """Register new converter."""
        cls._converters[field_type] = converter

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
        post_actions = []
        for field in model._meta.get_fields():
            if field.name in params:
                if params[field.name] is None:
                    continue
                for (converter_type, converter) in self._converters.items():
                    if isinstance(field, converter_type):
                        result = converter(self, field, params[field.name])
                        post_actions.extend(result.post_actions)
                        if not result.pass_field_value:
                            params.pop(field.name)
                        else:
                            params[field.name] = result.field_value
                        break
        return post_actions

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


class ObjManagerMixin:
    """Mixin for easy test object creation."""

    object_manager = None

    def setUp(self):
        """Set test environment up."""
        self.object_manager = ObjectManager()
        super().setUp()
