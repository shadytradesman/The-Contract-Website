#There's probably a better way to do this.
from django.shortcuts import _get_queryset


def get_queryset_size(klass,  *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        obj_query = queryset.filter(*args, **kwargs)
    except AttributeError:
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument get_queryset_size() must be a Model, Manager, or "
            "QuerySet, not '%s'." % klass__name
        )
    if not obj_query:
        return 0
    return obj_query.count()

def get_object_or_none(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except AttributeError:
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_object_or_none() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    except queryset.model.DoesNotExist:
        return None