# invocationLogger.py

#/***************************************************************************
# *  Copyright (C) 2015 Daniel Mueller (deso@posteo.net)                    *
# *                                                                         *
# *  This program is free software: you can redistribute it and/or modify   *
# *  it under the terms of the GNU General Public License as published by   *
# *  the Free Software Foundation, either version 3 of the License, or      *
# *  (at your option) any later version.                                    *
# *                                                                         *
# *  This program is distributed in the hope that it will be useful,        *
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of         *
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          *
# *  GNU General Public License for more details.                           *
# *                                                                         *
# *  You should have received a copy of the GNU General Public License      *
# *  along with this program.  If not, see <http://www.gnu.org/licenses/>.  *
# ***************************************************************************/

"""Functionality for logging an object's method invocations."""

from functools import (
  wraps,
)
from itertools import (
  chain,
)


class InvocationLogger(type):
  """A meta class used for logging method invocations."""
  def __new__(metaCls, name, bases, namespace, *args, **kwargs):
    """Constructor for a new class.

      Create a new class by intercepting all methods matching certain
      criteria with wrapped ones. Note that the additional arguments
      (args and kwargs) are required for argument passing to the meta
      class to work correctly.
    """
    # Do not include 'metaCls' in the replacement -- it is a meta class
    # and of no value for us here.
    for base in bases:
      InvocationLogger._overwriteMethods(base, namespace)

    return type.__new__(metaCls, name, bases, namespace)


  def __init__(self, *args, **kwargs):
    """Initialize the meta class object."""
    super().__init__(self)
    self.__meta_logger__ = kwargs['logger']


  @staticmethod
  def _wrap(function):
    """Wrap the given function."""
    @wraps(function)
    def wrapper(instance, *args, **kwargs):
      """Wrap a function and add proper logging."""
      def stringify(*args, **kwargs):
        """Convert positional and keyword arguments into a string."""
        # Convert the positional arguments in 'args' and the keyword
        # arguments in kwargs into strings.
        t = map(str, list(args))
        d = map(lambda x: '%s=%s' % x, kwargs.items())
        # Now chain the two iterables together and connect all the
        # strings by a comma.
        return ', '.join(chain(t, d))

      class_name = instance.__meta_original_classname__
      prefix = "%s.%s" % (class_name, function.__name__)
      logger = instance.__meta_logger__
      logger("%s(%s)", prefix, stringify(*args, **kwargs))
      try:
        result = function(instance, *args, **kwargs)
      except BaseException as e:
        logger("%s: raised %s (\"%s\")", prefix, type(e).__name__, str(e))
        raise

      logger("%s: %s", prefix, result)
      return result

    return wrapper


  @staticmethod
  def _overwriteMethods(cls, namespace):
    """Overwrite methods of a certain pattern in the given class."""
    for obj in dir(cls):
      # We only care for objects that have not been wrapped and are
      # only interested in public functions.
      # TODO: We might want to support white and/or black lists here.
      if not obj in namespace and not obj.startswith('_'):
        attr = getattr(cls, obj)
        # TODO: Right now we do not support logging of properties. Check
        #       if we require this functionality.
        if callable(attr):
          # Replace the method with a wrapped version.
          namespace[obj] = InvocationLogger._wrap(attr)

    # Recurse down into all base classes.
    for base in cls.__bases__:
      InvocationLogger._overwriteMethods(base, namespace)


def Logged(cls, logger):
  """Wrap a class to include proper logging of method calls."""
  # TODO: It would be best to use the type() built-in here. However, it
  #       is unclear how to incorporate meta classes (and passing of
  #       arguments to the same) into it.
  class __Proxy(cls, metaclass=InvocationLogger, logger=logger):
    """Proxy class required for proper interception."""
    # For appropriate logging we want to store the name of the wrapped class.
    # TODO: We might want to check if we can simply infer the original
    #       class name from the instance we got passed in to the wrapped
    #       call.
    __meta_original_classname__ = cls.__name__

  return __Proxy
