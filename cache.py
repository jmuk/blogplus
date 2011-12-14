# coding: utf-8

from functools import wraps

class _Cache:
  """Cache holds some data on-memory for performance."""
  def __init__(self):
    self._caches = {}

  def clear_cache(self):
    self._caches = {}

  # decorator method.
  def cached(self, key):
    """Don't care the difference of parameters for implementation easiness."""
    def cache_decorator(func):
      @wraps(func)
      def actual_func(*args):
        if key in self._caches:
          return self._caches[key]
        result = func(*args)
        self._caches[key] = result
        return result
      return actual_func
    return cache_decorator


_cache = _Cache()

cached = _cache.cached
clear_cache = _cache.clear_cache
