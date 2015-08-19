# testInvocationLogger.py

#/***************************************************************************
# *   Copyright (C) 2015 Daniel Mueller (deso@posteo.net)                   *
# *                                                                         *
# *   This program is free software: you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation, either version 3 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU General Public License for more details.                          *
# *                                                                         *
# *   You should have received a copy of the GNU General Public License     *
# *   along with this program.  If not, see <http://www.gnu.org/licenses/>. *
# ***************************************************************************/

"""Tests for the invocation logging facility."""

from abc import (
  ABCMeta,
  abstractmethod,
)
from unittest import (
  main,
  TestCase,
)
from unittest.mock import (
  call,
  MagicMock,
)
from logger import (
  Logged,
  LoggedObj,
)


class _Base:
  """A dummy base class."""
  def baseMethod1(self, arg1, arg2=None):
    """A method accepting up to three arguments."""
    return arg1 + arg2


class _Object(_Base):
  """A dummy object with a couple of public methods."""
  def method1(self):
    """A method accepting no parameters and returning nothing."""
    pass


  def method2(self, arg):
    """A method accepting a single parameter and returning it."""
    return arg


  def method3(self, arg1, arg2):
    """A method accepting two parameters and returning their "sum"."""
    return arg1 + arg2


  def method4(self):
    """A method that raises an exception."""
    raise RuntimeError("exception")


  def method5(self, foo=None):
    """A method that accepts a keyword argument."""
    return 2 * foo


class InvocationLoggerTest(metaclass=ABCMeta):
  """Test case mixin for the invocation logger facility."""
  @abstractmethod
  def createObject(self):
    """Create an object to run our tests on."""
    pass


  def setUp(self):
    """Set up a test harness, create a test object."""
    self._logger = MagicMock()
    self._object = self.createObject(self._logger)


  def testMethodInvocationNoArgumentsNoReturn(self):
    """Verify that a method without arguments and no return value is treated correctly."""
    expected_calls = [
      call('%s(%s)', '_Object.method1', ''),
      call('%s: %s', '_Object.method1', None),
    ]

    self.assertIsNone(self._object.method1())
    self.assertEqual(self._logger.call_args_list, expected_calls)


  def testMethodInvocationWithArgumentAndReturn(self):
    """Verify that a method with one argument is treated correctly."""
    argument = 'hello-test'
    expected_calls = [
      call('%s(%s)', '_Object.method2', argument),
      call('%s: %s', '_Object.method2', argument),
    ]

    self.assertEqual(self._object.method2(argument), argument)
    self.assertEqual(self._logger.call_args_list, expected_calls)


  def testMethodInvocationWithMultipleArguments(self):
    """Verify that a method with multiple argument is treated correctly."""
    arg1 = 24
    arg2 = 42
    result = arg1 + arg2

    expected_calls = [
      call('%s(%s)', '_Object.method3', '%d, %d' % (arg1, arg2)),
      call('%s: %s', '_Object.method3', result),
    ]

    self.assertEqual(self._object.method3(arg1, arg2), result)
    self.assertEqual(self._logger.call_args_list, expected_calls)


  def testMethodInvocationRaises(self):
    """Verify that a method that raises an exception is logged as expected."""
    expected_calls = [
      call('%s(%s)', '_Object.method4', ''),
      call('%s: raised %s ("%s")', '_Object.method4', 'RuntimeError', 'exception'),
    ]

    with self.assertRaises(RuntimeError):
      self._object.method4()

    self.assertEqual(self._logger.call_args_list, expected_calls)


  def testMethodInvocationWithKeywordArgument(self):
    """Verify that a method with a keyword argument is treated correctly."""
    expected_calls = [
      call('%s(%s)', '_Object.method5', 'foo=test'),
      call('%s: %s', '_Object.method5', 'testtest'),
    ]

    self.assertEqual(self._object.method5(foo='test'), 'testtest')
    self.assertEqual(self._logger.call_args_list, expected_calls)


  def testBaseMethodInvocation(self):
    """Verify that methods in the base class are wrapped properly as well."""
    arg1 = 2
    arg2 = 4
    result = arg1 + arg2

    expected_calls = [
      call('%s(%s)', '_Object.baseMethod1', '%d, arg2=%d' % (arg1, arg2)),
      call('%s: %s', '_Object.baseMethod1', result),
    ]

    self.assertEqual(self._object.baseMethod1(arg1, arg2=arg2), result)
    self.assertEqual(self._logger.call_args_list, expected_calls)


# Note that the order of inheritance is important. InvocationLoggerTest
# provides a setUp method and at some point TestCase (or some related
# class) causes it to be invoked. So InvocationLoggerTest needs to be
# first in the attribute lookup order.
class TestInvocationLoggerForClass(InvocationLoggerTest, TestCase):
  """Test case for the invocation logger facility for classes."""
  def createObject(self, logger):
    """Create an object to run our tests on."""
    return Logged(_Object, logger)()


class TestInvocationLoggerForObject(InvocationLoggerTest, TestCase):
  """Test case for the invocation logger facility for objects."""
  def createObject(self, logger):
    """Create an object to run our tests on."""
    return LoggedObj(_Object(), logger)


class TestInvocationLoggerWithMeta(TestCase):
  """Test to verify the invocation logger's compliance with meta classes."""
  def testLoggedUsageOnClassWithMetaClass(self):
    """Verify that the Logged() function works correctly with meta classes."""
    class MetaBar(type):
      """A very simple dummy meta class."""
      pass

    class Foo(metaclass=MetaBar):
      """A dummy class already using a meta class."""
      def foo(self):
        """Some method returning 42."""
        return 42

    expected_calls = [
      call('%s(%s)', 'Foo.foo', ''),
      call('%s: %s', 'Foo.foo', 42),
    ]

    logger = MagicMock()
    foo = Logged(Foo, logger)()

    self.assertEqual(foo.foo(), 42)
    self.assertEqual(logger.call_args_list, expected_calls)


if __name__ == '__main__':
  main()
