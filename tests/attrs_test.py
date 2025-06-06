# Copyright 2024 The JAX Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from dataclasses import dataclass
import itertools as it

from absl.testing import absltest
from absl.testing import parameterized
import numpy as np

import jax
import jax.numpy as jnp

from jax._src import config
from jax._src import test_util as jtu
from jax._src.util import safe_zip, safe_map

from jax._src import attrs
from jax.experimental.attrs import (
    jax_setattr, jax_getattr, jax_appendattr, Box, List)

config.parse_flags_with_absl()

map, unsafe_map = safe_map, map
zip, unsafe_zip = safe_zip, zip

@dataclass
class Thing:
  x: float
  __hash__ = object.__hash__
  __eq__ = object.__eq__

attrs.register(Thing)  # enables passing as arg into jitted function

class AttrsTest(jtu.JaxTestCase):

  @parameterized.parameters([True, False])
  def test_jit_basic(self, jit: bool):
    thing = Thing(1.0)

    def double_it() -> None:
      cur_x = jax_getattr(thing, "x")
      jax_setattr(thing, "x", cur_x * 2)

    if jit:
      double_it = jax.jit(double_it)

    self.assertEqual(thing.x, 1.0)
    double_it()
    self.assertEqual(thing.x, 2.0)
    double_it()
    self.assertEqual(thing.x, 4.0)
    double_it()
    self.assertEqual(thing.x, 8.0)
    double_it()
    self.assertEqual(thing.x, 16.0)

  def test_setattr_doesnt_leak(self):
    thing = Thing(1.0)

    @jax.jit
    def f(x):
      jax_setattr(thing, 'x', x)
      raise Exception

    try: f(1.)
    except: pass
    self.assertNotIsInstance(thing.x, jax.core.Tracer)


  @parameterized.parameters([True, False])
  def test_jit_basic_tree(self, jit: bool):
    thing = Thing((1.0, 2.0))

    def double_it() -> None:
      (cur_x, cur_y) = jax_getattr(thing, "x")
      jax_setattr(thing, "x", (cur_x * 2, cur_y * 2))

    if jit:
      double_it = jax.jit(double_it)

    self.assertEqual(thing.x, (1.0, 2.0))
    double_it()
    self.assertEqual(thing.x, (2.0, 4.0))
    double_it()
    self.assertEqual(thing.x, (4.0, 8.0))
    double_it()
    self.assertEqual(thing.x, (8.0, 16.0))
    double_it()
    self.assertEqual(thing.x, (16.0, 32.0))

  @parameterized.parameters([True, False])
  def test_jit_basic_tree_changes(self, jit: bool):
    thing = Thing(None)
    count = 0

    def double_it() -> None:
      nonlocal count
      count += 1
      maybe_x = jax_getattr(thing, "x")
      x = 1.0 if maybe_x is None else maybe_x
      jax_setattr(thing, "x", 2 * x)

    if jit:
      double_it = jax.jit(double_it)

    self.assertEqual(thing.x, None)
    double_it()
    self.assertEqual(thing.x, 2.0)
    self.assertEqual(count, 1)
    double_it()
    self.assertEqual(thing.x, 4.0)
    self.assertEqual(count, 2)
    double_it()
    self.assertEqual(thing.x, 8.0)
    self.assertEqual(count, 2 + (not jit))

  def test_jit_basic_tree_changes_multiple(self):
    thing1 = Thing(None)
    thing2 = Thing(0)
    count = 0

    @jax.jit
    def double_it() -> None:
      nonlocal count
      count += 1

      x1 = jax_getattr(thing1, "x")
      if x1 is None:
        jax_setattr(thing1, 'x', (None,))
      elif isinstance(x1, tuple):
        # depend on a new value
        jax_setattr(thing1, 'x', jax_getattr(thing2, 'x') + 1)
      else:
        jax_setattr(thing2, 'x', jax_getattr(thing1, 'x'))
        jax_setattr(thing1, 'x', None)

    self.assertEqual(thing1.x, None)
    self.assertEqual(thing2.x, 0)
    double_it()
    self.assertEqual(thing1.x, (None,))
    self.assertEqual(thing2.x, 0)
    self.assertEqual(count, 1)
    double_it()
    self.assertEqual(thing1.x, 1)
    self.assertEqual(thing2.x, 0)
    self.assertEqual(count, 2)
    double_it()
    self.assertEqual(thing1.x, None)
    self.assertEqual(thing2.x, 1)
    self.assertEqual(count, 3)
    double_it()
    self.assertEqual(thing1.x, (None,))
    self.assertEqual(thing2.x, 1)
    self.assertEqual(count, 3)
    double_it()
    self.assertEqual(thing1.x, 2)
    self.assertEqual(thing2.x, 1)
    self.assertEqual(count, 3)
    double_it()
    self.assertEqual(thing1.x, None)
    self.assertEqual(thing2.x, 2)
    self.assertEqual(count, 3)

  def test_jit_nesting_basic(self):
    thing = Thing(1.0)

    @jax.jit
    @jax.jit
    def double_it() -> None:
      cur_x = jax_getattr(thing, "x")
      jax_setattr(thing, "x", cur_x * 2)

    self.assertEqual(thing.x, 1.0)
    double_it()
    self.assertEqual(thing.x, 2.0)
    double_it()
    self.assertEqual(thing.x, 4.0)
    double_it()
    self.assertEqual(thing.x, 8.0)
    double_it()
    self.assertEqual(thing.x, 16.0)

  def test_jit_consts_and_args(self):
    thing = Thing(1.0)

    @jax.jit
    def double_it(y) -> None:
      cur_x = jax_getattr(thing, "x")
      jax_setattr(thing, "x", cur_x * 2)
      return jnp.cos(np.arange(3.) * cur_x * y)

    self.assertEqual(thing.x, 1.0)
    double_it(2.)
    self.assertEqual(thing.x, 2.0)
    double_it(2.)
    self.assertEqual(thing.x, 4.0)
    double_it(2.)
    self.assertEqual(thing.x, 8.0)
    double_it(2.)
    self.assertEqual(thing.x, 16.0)

  def test_jit_transpose_basic(self):
    thing = Thing(jnp.array(2.0))

    @jax.custom_vjp
    def foo(x):
      return x

    def foo_fwd(x):
      return x, None

    def foo_bwd(x, g):
      jax_setattr(thing, 'x', g)
      return g,

    foo.defvjp(foo_fwd, foo_bwd)

    foo(3.14)
    self.assertEqual(thing.x, 2.0)

    jax.grad(foo)(3.14)
    self.assertEqual(thing.x, 1.0)

    thing.x = jnp.array(3.14)
    self.assertEqual(thing.x, 3.14)

    jax.jit(jax.grad(foo))(3.14)
    self.assertEqual(thing.x, 1.0)

    thing.x = jnp.array(2.718)
    self.assertEqual(thing.x, 2.718)

    jax.grad(jax.jit(lambda x: jnp.sin(foo(x))))(3.0)
    self.assertAllClose(thing.x, -0.9899925, atol=1e-5, rtol=1e-5, check_dtypes=False)

    thing.x = jnp.array(3.14)
    self.assertEqual(thing.x, 3.14)

    def bar(x):
      out = jnp.sin(foo(x))
      jax_setattr(thing, 'x', 5.0)
      return out

    jax.grad(jax.jit(bar))(3.0)
    self.assertAllClose(thing.x, -0.9899925, atol=1e-5, rtol=1e-5, check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_scan_basic(self, jit: bool):
    thing = Thing(1.0)

    def double_it_10():
      def body(_, __):
        cur_x = jax_getattr(thing ,"x")
        jax_setattr(thing, "x", cur_x * 2.0)
        return None, None
      _, _ = jax.lax.scan(body, None, None, length=10)

    if jit:
      double_it_10 = jax.jit(double_it_10)

    double_it_10()
    self.assertAllClose(thing.x, 1024., check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_scan_basic_pytree(self, jit):
    class Thing: ...
    thing = Thing()
    thing.x = (1.0, 1.0)

    def double_it_10():
      def body(_, __):
        cur_x, _ = jax_getattr(thing ,"x")
        jax_setattr(thing, "x", (cur_x * 2.0, 3.0))
        return None, None
      _, _ = jax.lax.scan(body, None, None, length=10)

    if jit:
      double_it_10 = jax.jit(double_it_10)

    double_it_10()
    self.assertAllClose(thing.x[0], 1024., check_dtypes=False)
    self.assertAllClose(thing.x[1],    3., check_dtypes=False)

  def test_scan_basic_consts_and_args(self):
    thing = Thing(1.0)

    def double_it_10(y):
      def body(i, x):
        cur_x = jax_getattr(thing ,"x")
        jax_setattr(thing, "x", cur_x * 2.0)
        return i + 1, (y, y)
      _, _ = jax.lax.scan(body, 0, jnp.arange(10))

    jax.jit(double_it_10)(jnp.arange(3.))
    self.assertAllClose(thing.x, 1024., check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_scan_transpose_basic(self, jit: bool):
    thing = Thing(1.0)

    @jax.custom_vjp
    def foo(x):
      return x

    def foo_fwd(x):
      return x, None

    def foo_bwd(x, g):
      jax_setattr(thing, 'x', 2 * jax_getattr(thing, 'x') * g)
      return g,

    foo.defvjp(foo_fwd, foo_bwd)


    def double_it_10(x):
      def body(x, __):
        return foo(x), None
      x, _ = jax.lax.scan(body, x, None, length=10)
      return x

    if jit:
      double_it_10 = jax.jit(double_it_10)

    double_it_10(1.0)
    self.assertAllClose(thing.x, 1., check_dtypes=False)

    jax.grad(double_it_10)(1.0)
    self.assertAllClose(thing.x, 1024., check_dtypes=False)

  def test_arg_to_jit(self):
    self.skipTest("regressed this experimental feature")  # TODO(mattjj)
    thing = Thing(1.0)
    count = 0

    @jax.jit
    def f(obj, x):
      nonlocal count
      count += 1
      jax_setattr(obj, 'x', x)

    f(thing, 2.0)  # don't crash!
    self.assertAllClose(thing.x, 2.0, check_dtypes=False)
    f(thing, 3.0)
    self.assertAllClose(thing.x, 3.0, check_dtypes=False)
    self.assertEqual(count, 1)

  def test_tracer_lifetime_bug(self):
    # regression test for https://github.com/jax-ml/jax/issues/20082
    class StatefulRNG:
      key: jax.Array

      def __init__(self, key: jax.Array):
        self.key = key

      def split(self) -> jax.Array:
        key = jax_getattr(self, "key")
        new_key, returned_key = jax.random.split(key)
        jax_setattr(self, "key", new_key)
        return returned_key

    rng = StatefulRNG(jax.random.key(0))

    def jitted():
      rng.split()
      rng.split()

    jax.jit(jitted)()  # don't crash

  def test_scan_carry(self):
    class A:
      ...

    a = A()

    jax_setattr(a, 'x', jnp.zeros(3))

    def body(i, _):
      x = jax_getattr(a, 'x')
      x = x.at[i].set(x[i] + 1)
      jax_setattr(a, 'x', x)
      return i + 1, None
    _, _ = jax.lax.scan(body, 0, None, length=3)  # don't crash

  @parameterized.parameters([True, False])
  def test_setattr_doesnt_exist(self, jit):
    class Thing:
      ...
    thing = Thing()

    def f(x):
      assert (not jit) or tracing_is_ok
      jax_setattr(thing, 'x', x)

    if jit:
      f = jax.jit(f)

    tracing_is_ok = True
    self.assertFalse(hasattr(thing, 'x'))
    f(1.0)
    self.assertEqual(thing.x, 1.0)
    f(2.0)
    self.assertEqual(thing.x, 2.0)

    tracing_is_ok = False
    f(3.0)
    self.assertEqual(thing.x, 3.0)

    del thing.x
    f(4.0)
    self.assertEqual(thing.x, 4.0)

    tracing_is_ok = True
    f(5)
    self.assertEqual(thing.x, 5)

  def test_setattr_doesnt_exist_doesnt_leave_sentinel_around(self):
    class Thing:
      ...
    thing = Thing()

    def f(x):
      jax_setattr(thing, 'x', x)

    jax.make_jaxpr(f)(3.)
    self.assertFalse(hasattr(thing, 'x'))
    tracing_ok = True
    f(0.0)
    self.assertAllClose(thing.x, 0.)
    tracing_ok = False
    f(1.0)
    self.assertAllClose(thing.x, 1.)

  @parameterized.parameters(it.product([False, True], repeat=2))
  def test_appendattr_basic(self, jit, initialized):
    class Thing:
      ...
    thing = Thing()

    if initialized:
      thing.x = jnp.arange(0.)

    def f(x):
      assert (not jit) or tracing_ok
      jax_appendattr(thing, 'x', x)
      jax_appendattr(thing, 'x', x + 1)

    if jit:
      f = jax.jit(f)

    tracing_ok = True
    f(0.0)
    self.assertAllClose(thing.x, jnp.array([0., 1.]))
    tracing_ok = False
    f(2.0)
    self.assertAllClose(thing.x, jnp.array([0., 1., 2., 3.]))
    f(4.0)
    self.assertAllClose(thing.x, jnp.array([0., 1., 2., 3., 4., 5.]))

  @parameterized.parameters(it.product([False, True], repeat=2))
  def test_appendattr_constant(self, jit, initialized):
    class Thing: ...
    thing = Thing()

    if initialized:
      thing.x = jnp.arange(0.)

    def f():
      assert (not jit) or tracing_ok
      jax_appendattr(thing, 'x', 0.0)
      jax_appendattr(thing, 'x', 1.0)

    if jit:
      f = jax.jit(f)

    tracing_ok = True
    f()
    self.assertAllClose(thing.x, jnp.array([0., 1.]))
    tracing_ok = False
    f()
    self.assertAllClose(thing.x, jnp.array([0., 1., 0., 1.]))

  @parameterized.parameters([True, False])
  def test_appendattr_getattr_errors(self, initialized):
    class Thing: ...
    thing = Thing()

    if initialized:
      thing.x = jnp.arange(0.)

    @jax.jit
    def f(x):
      jax_appendattr(thing, 'x', x)
      jax_getattr(thing, 'x')

    with self.assertRaisesRegex(TypeError, "can't read/write"):
      f(1.0)

    @jax.jit
    def g(x):
      jax_setattr(thing, 'x', x)
      jax_appendattr(thing, 'x', x)

    with self.assertRaisesRegex(TypeError, "can't append"):
      g(1.0)

    if initialized:
      self.assertNotIsInstance(thing.x, jax.core.Tracer)
    else:
      self.assertFalse(hasattr(thing, 'x'))

  @parameterized.parameters(it.product([False, True], repeat=2))
  def test_appendattr_dtype_disagreement(self, jit, initialized):
    class Thing: ...
    thing = Thing()

    if initialized:
      thing.x = jnp.array([], 'float32')

    def f(x):
      jax_appendattr(thing, 'x', x)
      jax_appendattr(thing, 'x', x.astype('complex64'))

    if jit:
      f = jax.jit(f)

    msg = "can only append to attr x with values of trailing shape "
    msg += "float32" if initialized else "int32"
    with self.assertRaisesRegex(TypeError, msg):
      f(jnp.array(1, 'int32'))

  @parameterized.parameters(it.product([False, True], repeat=2))
  def test_appendattr_shape_disagreement(self, jit, initialized):
    class Thing: ...
    thing = Thing()

    if initialized:
      thing.x = jnp.array([])

    def f(x):
      jax_appendattr(thing, 'x', x)
      jax_appendattr(thing, 'x', jnp.stack([x, x]))

    if jit:
      f = jax.jit(f)

    msg = "can only append to attr x with values of trailing shape"
    with self.assertRaisesRegex(TypeError, msg):
      f(1)

  @parameterized.parameters(it.product([False, True], repeat=2))
  def test_appendattr_scan(self, jit, initialized):
    class Thing: ...
    thing = Thing()

    if initialized:
      thing.x = jnp.array([])

    def f():
      def body(c, x):
        jax_appendattr(thing, 'x', 2 * x)
        jax_appendattr(thing, 'x', 2 * x + 1)
        return c, ()
      _, () = jax.lax.scan(body, 0, jnp.arange(3.))

    if jit:
      f = jax.jit(f)

    f()

    self.assertAllClose(thing.x, jnp.array([0., 1., 2., 3., 4., 5.]))

  @parameterized.parameters(it.product([False, True], repeat=2))
  def test_appendattr_scan_vjp(self, jit, initialized):
    class Thing: ...
    thing = Thing()

    if initialized:
      thing.y_bar = jnp.array([])

    def f(x):
      def body(c, _):
        return 0.5 * g(2 * c), ()
      y, _ = jax.lax.scan(body, x, (), length=5)
      return y

    if jit:
      f = jax.jit(f)

    @jax.custom_vjp
    def g(x):
      return x

    def g_fwd(x):
      return g(x), None

    def g_bwd(_, y_bar):
      jax_appendattr(thing, 'y_bar', y_bar)
      return y_bar,

    g.defvjp(g_fwd, g_bwd)
    jax.grad(f)(3.)

    self.assertAllClose(thing.y_bar, jnp.array([0.5] * 5))


class AttrsJVPTest(jtu.JaxTestCase):

  @parameterized.parameters([True, False])
  def test_jvp_basic(self, jit):
    thing = Thing(2.0)

    def f():
      x = jax_getattr(thing, 'x')
      x = jnp.sin(x)
      jax_setattr(thing, 'x', x)

    if jit:
      f = jax.jit(f)

    _, _, attr_tangents = attrs.jvp(f, (), (), [(thing, 'x', 1.0)])
    self.assertAllClose(thing.x, jnp.sin(2.0), check_dtypes=False)
    (thing_, attr_, tangent_), = attr_tangents
    self.assertIs(thing, thing_)
    self.assertEqual(attr_, 'x')
    self.assertAllClose(tangent_, jnp.cos(2.0), check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_jvp_clobber(self, jit):
    thing = Thing(2.0)

    def f():
      x = jax_getattr(thing, 'x')
      x = jnp.sin(2.0)
      jax_setattr(thing, 'x', x)

    if jit:
      f = jax.jit(f)

    _, _, attr_tangents = attrs.jvp(f, (), (), [(thing, 'x', 1.0)])
    self.assertAllClose(thing.x, jnp.sin(2.0), check_dtypes=False)
    self.assertEmpty(attr_tangents)

  @parameterized.parameters([True, False])
  def test_jvp_nowrite(self, jit):
    thing = Thing(2.0)

    def f():
      x = jax_getattr(thing, 'x')

    if jit:
      f = jax.jit(f)

    _, _, attr_tangents = attrs.jvp(f, (), (), [(thing, 'x', 1.0)])
    self.assertAllClose(thing.x, 2.0, check_dtypes=False)
    (thing_, attr_, tangent_), = attr_tangents
    self.assertIs(thing, thing_)
    self.assertEqual(attr_, 'x')
    self.assertAllClose(tangent_, 1.0, check_dtypes=False)

  def test_jit_of_jvp(self):
    thing = Thing(2.0)

    def f():
      x = jax_getattr(thing, 'x')
      x = jnp.sin(x)
      jax_setattr(thing, 'x', x)

    @jax.jit
    def g():
      _, _, attr_tangents = attrs.jvp(f, (), (), [(thing, 'x', 1.0)])
      (thing_, attr_, tangent_), = attr_tangents
      self.assertIs(thing, thing_)
      self.assertEqual(attr_, 'x')
      return jax_getattr(thing, 'x'), tangent_

    x, tangent = g()
    self.assertAllClose(x, jnp.sin(2.0), check_dtypes=False)
    self.assertAllClose(tangent, jnp.cos(2.0), check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_jvp_higher_order(self, jit):
    thing = Thing(2.0)

    def f(y):
      x = jax_getattr(thing, 'x')
      w = jnp.tan(jnp.sin(y) * jnp.cos(x))
      z = jnp.tan(jnp.cos(y) * jnp.sin(x))
      jax_setattr(thing, 'x', z)
      return w
    if jit:
      f = jax.jit(f)

    def f_ref(x, y):
      w = jnp.tan(jnp.sin(y) * jnp.cos(x))
      z = jnp.tan(jnp.cos(y) * jnp.sin(x))
      return w, z

    x     = jax.random.normal(jax.random.key(0), (3,))
    x_dot = jax.random.normal(jax.random.key(1), (3,))
    y     = jax.random.normal(jax.random.key(2), (3,))
    y_dot = jax.random.normal(jax.random.key(3), (3,))

    setattr(thing, 'x', x)
    w, w_dot, [(_, _, z_dot)] = attrs.jvp(f, (y,), (y_dot,), [(thing, 'x', x_dot)])
    z = getattr(thing, 'x')

    (w_, z_), (w_dot_, z_dot_) = jax.jvp(f_ref, (x, y), (x_dot, y_dot))

    self.assertAllClose(w, w_, check_dtypes=False)
    self.assertAllClose(z, z_, check_dtypes=False)
    self.assertAllClose(w_dot, w_dot_, check_dtypes=False)
    self.assertAllClose(z_dot, z_dot_, check_dtypes=False)

    def g(x_dot, y, y_dot):
      w, w_dot, [(_, _, z_dot)] = attrs.jvp(f, (y,), (y_dot,), [(thing, 'x', x_dot)])
      return w, w_dot, z_dot

    def g_ref(x, x_dot, y, y_dot):
      (w, z), (w_dot, z_dot) = jax.jvp(f_ref, (x, y), (x_dot, y_dot))
      return w, w_dot, z, z_dot

    x_dot2    = jax.random.normal(jax.random.key(3), (3,))
    x_ddot    = jax.random.normal(jax.random.key(4), (3,))
    y_dot2    = jax.random.normal(jax.random.key(5), (3,))
    y_ddot    = jax.random.normal(jax.random.key(6), (3,))

    setattr(thing, 'x', x)
    (w, w_dot, z_dot), (w_dot2, w_ddot, z_ddot), [(_, _, z_dot2)] = \
        attrs.jvp(g, (x_dot, y, y_dot), (x_ddot, y_dot2, y_ddot),
                  [(thing, 'x', x_dot2)])
    z = getattr(thing, 'x')

    (w_, w_dot_, z_, z_dot_), (w_dot2_, w_ddot_, z_dot2_, z_ddot_) = \
        jax.jvp(g_ref, (x, x_dot, y, y_dot), (x_dot2, x_ddot, y_dot2, y_ddot))

    self.assertAllClose(     w,      w_, check_dtypes=False)
    self.assertAllClose(     z,      z_, check_dtypes=False)
    self.assertAllClose( w_dot,  w_dot_, check_dtypes=False)
    self.assertAllClose( z_dot,  z_dot_, check_dtypes=False)
    self.assertAllClose(w_dot2, w_dot2_, check_dtypes=False)
    self.assertAllClose(z_dot2, z_dot2_, check_dtypes=False)
    self.assertAllClose(w_ddot, w_ddot_, check_dtypes=False)
    self.assertAllClose(z_ddot, z_ddot_, check_dtypes=False)


class AttrsLinTest(jtu.JaxTestCase):

  @parameterized.parameters([True, False])
  def test_attr_output(self, jit):
    thing = Thing(1.0)

    def f(x, _):
      y = jnp.sin(x)
      jax_setattr(thing, 'x', y)

    if jit:
      f = jax.jit(f)

    out, f_lin = attrs.linearize(f, 3.0, 4.0)
    self.assertIsNone(out)
    self.assertAllClose(thing.x, jnp.sin(3.0), check_dtypes=False)

    out_dot, attr_tangents = f_lin(1.0, 2.0, attr_tangents={})
    self.assertIsNone(out_dot)
    self.assertAllClose(thing.x, jnp.sin(3.0))  # didn't change
    self.assertLen(attr_tangents, 1)
    self.assertAllClose(attr_tangents[(thing, 'x')], jnp.cos(3.0),
                        check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_attr_input(self, jit):
    thing = Thing(1.0)

    def f():
      x = jax_getattr(thing, 'x')
      return jnp.sin(x)

    if jit:
      f = jax.jit(f)

    out, f_lin = attrs.linearize(f, attrs=[(thing, 'x')])
    self.assertAllClose(out, jnp.sin(1.0), check_dtypes=False)

    out_dot, attr_tangents = f_lin(attr_tangents={(thing, 'x'): 2.0})
    self.assertAllClose(out_dot, 2. * jnp.cos(1.0), check_dtypes=False)
    self.assertLen(attr_tangents, 1)
    self.assertAllClose(attr_tangents[(thing, 'x')], 2.0, check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_attr_inout(self, jit):
    thing1 = Thing(1.0)
    thing2 = Thing(2.0)

    def f(x, y):
      z = jax_getattr(thing1, 'x')
      w = jax_getattr(thing2, 'x')
      out = jnp.sin(x * y * z * w)
      jax_setattr(thing1, 'x', out)
      jax_setattr(thing2, 'x', 2 * out)
      return 3 * out, 4 * out

    if jit:
      f = jax.jit(f)

    def f_ref(x, y, z, w):
      out = jnp.sin(x * y * z * w)
      return (3 * out, 4 * out), (out, 2 * out)

    out, f_lin = attrs.linearize(f, 3., 4., attrs=[(thing1, 'x'), (thing2, 'x')])
    expected = (3 * jnp.sin(1. * 2. * 3. * 4.),
                4 * jnp.sin(1. * 2. * 3. * 4.))
    self.assertAllClose(out, expected, check_dtypes=False)
    self.assertAllClose(thing1.x, jnp.sin(1. * 2. * 3. * 4.))
    self.assertAllClose(thing2.x, 2 * jnp.sin(1. * 2. * 3. * 4.))

    (out_ref, state_out_ref), f_lin_ref = jax.linearize(f_ref, 3., 4., 1., 2.)
    self.assertAllClose(out, out_ref, check_dtypes=False)
    self.assertAllClose((thing1.x, thing2.x), state_out_ref, check_dtypes=False)

    out_dot, attr_tangents = f_lin(1., 2.,
                                   attr_tangents={(thing1, 'x'): 5.,
                                                  (thing2, 'x'): 6.})
    self.assertAllClose(thing1.x, jnp.sin(1. * 2. * 3. * 4.))
    self.assertAllClose(thing2.x, 2 * jnp.sin(1. * 2. * 3. * 4.))
    (out_dot_ref, state_dot_ref) = f_lin_ref(1., 2., 5., 6.)
    self.assertAllClose(out_dot, out_dot_ref, check_dtypes=False)
    self.assertLen(attr_tangents, 2)
    self.assertAllClose(attr_tangents[(thing1, 'x')], state_dot_ref[0],
                        check_dtypes=False)
    self.assertAllClose(attr_tangents[(thing2, 'x')], state_dot_ref[1],
                        check_dtypes=False)

class AttrsVJPTest(jtu.JaxTestCase):

  @parameterized.parameters([True, False])
  def test_attr_input(self, jit):
    thing = Thing(1.0)

    def f():
      x = jax_getattr(thing, 'x')
      return jnp.sin(x)

    if jit:
      f = jax.jit(f)

    out, f_vjp = attrs.vjp(f, attrs=[(thing, 'x')])
    self.assertAllClose(out, jnp.sin(1.0), check_dtypes=False)

    arg_cts, attr_cotangents = f_vjp(1.0)
    self.assertEqual(arg_cts, ())
    self.assertLen(attr_cotangents, 1)
    self.assertAllClose(attr_cotangents[(thing, 'x')], jnp.cos(1.0),
                        check_dtypes=False)

  @parameterized.parameters([True, False])
  def test_attr_output(self, jit):
    thing = Thing(1.0)

    def f(x, _):
      y = jnp.sin(x)
      jax_setattr(thing, 'x', y)

    if jit:
      f = jax.jit(f)

    out, f_vjp = attrs.vjp(f, 3.0, 4.0)
    self.assertIsNone(out)
    self.assertAllClose(thing.x, jnp.sin(3.0), check_dtypes=False)

    arg_cts, attr_cotangents = f_vjp(None, attr_cotangents={(thing, 'x'): 2.0})
    self.assertAllClose(arg_cts, (2 * jnp.cos(3.0), 0.), check_dtypes=False)
    self.assertLen(attr_cotangents, 0)

  @parameterized.parameters([True, False])
  def test_attr_inout(self, jit):
    thing1 = Thing(1.0)
    thing2 = Thing(2.0)

    def f(x, y):
      z = jax_getattr(thing1, 'x')
      w = jax_getattr(thing2, 'x')
      out = jnp.sin(x * y * z * w)
      jax_setattr(thing1, 'x', out)
      jax_setattr(thing2, 'x', 2 * out)
      return 3 * out, 4 * out

    if jit:
      f = jax.jit(f)

    def f_ref(x, y, z, w):
      out = jnp.sin(x * y * z * w)
      return (3 * out, 4 * out), (out, 2 * out)

    out, f_vjp = attrs.vjp(f, 3., 4., attrs=[(thing1, 'x'), (thing2, 'x')])
    (out_ref, state_out_ref), f_vjp_ref = jax.vjp(f_ref, 3., 4., 1., 2.)
    self.assertAllClose(out, out_ref, check_dtypes=False)
    self.assertAllClose((thing1.x, thing2.x), state_out_ref, check_dtypes=False)

    in_bar, attr_cotangents = f_vjp((1., 2.),
                                    attr_cotangents={(thing1, 'x'): 5.,
                                                     (thing2, 'x'): 6.})
    in_bar_ref_ = f_vjp_ref(((1., 2.), (5., 6.)))
    in_bar_ref, attr_cotangents_ref = in_bar_ref_[:2], in_bar_ref_[2:]
    self.assertAllClose(in_bar, in_bar_ref, check_dtypes=False)
    self.assertLen(attr_cotangents, 2)
    self.assertAllClose(attr_cotangents[(thing1, 'x')], attr_cotangents_ref[0],
                        check_dtypes=False)
    self.assertAllClose(attr_cotangents[(thing2, 'x')], attr_cotangents_ref[1],
                        check_dtypes=False)


class BoxTest(jtu.JaxTestCase):

  def test_jit_arg(self):
    @jax.jit
    def f(box, x):
      assert tracing_ok
      box.set(box.get() + x)

    tracing_ok = True
    box1 = Box(1.0)
    f(box1, 1.)
    self.assertAllClose(box1.get(), 2.0)

    tracing_ok = False
    box2 = Box(2.0)
    f(box2, 2.)
    self.assertAllClose(box2.get(), 4.0)

  def test_jit_arg_in_pytree(self):
    @jax.jit
    def f(dct, x):
      assert tracing_ok
      box = dct['box']
      box.set(box.get() + x)

    tracing_ok = True
    box1 = Box(1.0)
    f({'box': box1, 'a': 1.0}, 1.)
    self.assertAllClose(box1.get(), 2.0)

    tracing_ok = False
    box2 = Box(2.0)
    f({'box': box2, 'a': 2.0}, 2.)
    self.assertAllClose(box2.get(), 4.0)

    tracing_ok = True
    box3 = Box(3)  # int, dtype changed
    f({'box': box3, 'a': 2.0}, 2.)
    self.assertAllClose(box3.get(), 5.0)

  def test_jit_closure(self):
    @jax.jit
    def f(x):
      box.set(box.get() + x)

    box = Box(1.0)
    f(2.0)
    self.assertAllClose(box.get(), 3.0)

    @jax.jit
    def g(x):
      f(x)

    g(3.0)
    self.assertAllClose(box.get(), 6.0)

  def test_jit_closure_nested(self):
    @jax.jit
    def h(x):
      box = Box(x)

      @jax.jit
      def k(x):
        box.set(box.get() + x)

      k(1.0)
      k(1.0)
      return box.get()

    ans = h(2.0)
    self.assertAllClose(ans, 4.0)

  @parameterized.parameters([False, True])
  def test_jvp_closure_stop_gradient(self, jit):
    box = Box(1.0)

    def f(x):
      y = 2 * x
      box.set(box.get() + jax.lax.stop_gradient(y))
      return y

    if jit:
      f = jax.jit(f)

    y, y_dot = jax.jvp(f, (1.0,), (1.0,))
    self.assertAllClose(y, 2.0)
    self.assertAllClose(y_dot, 2.0)
    self.assertAllClose(box.get(), 3.0)

  @parameterized.parameters([False, True])
  def test_jvp_arg(self, jit):
    def f(box, x):
      box.set(box.get() + x)
      return x

    if jit:
      f = jax.jit(f)

    box = Box(5.0)
    box_dot = Box(1.0)
    y, y_dot = jax.jvp(f, (box, 2.), (box_dot, 1.))
    self.assertAllClose(y, 2.0)
    self.assertAllClose(y_dot, 1.0)
    self.assertAllClose(box.get(), 7.0)
    self.assertAllClose(box_dot.get(), 2.0)

  @parameterized.parameters([False, True])
  def test_custom_vjp_plumbing(self, jit):
    box = Box(0.0)

    @jax.custom_vjp
    def foo(x):
      return x
    def foo_fwd(x):
      return foo(x), None
    def foo_bwd(_, g):
      box.set(g)
      return g,
    foo.defvjp(foo_fwd, foo_bwd)

    def f(x):
      x = 2 * x
      x = foo(x)
      x = 2 * x
      return x

    if jit:
      f = jax.jit(f)

    jax.grad(f)(1.0)
    self.assertAllClose(box.get(), 2.0)

  @parameterized.parameters([False, True])
  def test_grad_closure_stop_gradient(self, jit):
    box = Box(0.0)

    def f(x):
      y = x * 2
      box.set(box.get() + jax.lax.stop_gradient(y))
      return y

    if jit:
      f = jax.jit(f)

    g = jax.grad(f)(1.0)
    self.assertAllClose(g, 2.0)
    self.assertAllClose(box.get(), 2.0)

  @parameterized.parameters([False, True])
  def test_scan_basic(self, jit):
    box = Box(1.0)

    def double_it_10():
      def body(_, __):
        box.set(box.get() * 2)
        return None, None
      _, _ = jax.lax.scan(body, None, None, length=10)

    if jit:
      double_it_10 = jax.jit(double_it_10)

    double_it_10()
    self.assertAllClose(box.get(), 1024., check_dtypes=False)

  def test_error_passing_multiple_times_to_jit(self):

    @jax.jit
    def f(box1, box2):
      ...

    b = Box(1.0)
    with self.assertRaisesRegex(ValueError, "a Box instance can't be passed"):
      f(b, b)

  # TODO(mattjj): re-enable this test
  # def test_error_returning_from_jit(self):
  #   @jax.jit
  #   def f():
  #     return {'a': Box(1.0)}

  #   with self.assertRaisesRegex(ValueError, "a Box instance can't be returned"):
  #     f()


class ListTest(jtu.JaxTestCase):

  def test_eager(self):
    lst = List()
    lst.append(1.0)
    lst.append(2.0)
    lst.append(3.0)
    self.assertAllClose(lst.get(), [1., 2., 3.])

  def test_jit_arg(self):
    @jax.jit
    def f(lst, x):
      assert tracing_ok
      lst.append(1.0)
      lst.append(2.0)
      lst.append({'c': x + 3.0})

    tracing_ok = True
    lst1 = List()
    f(lst1, 0)
    self.assertAllClose(lst1.get(), [1., 2., {'c': 3.}])

    tracing_ok = False
    lst2 = List()
    lst2.append(0.)
    f(lst2, 1)
    self.assertAllClose(lst2.get(), [0., 1., 2., {'c': 4.}])

  def test_jit_closure(self):
    lst = List()

    @jax.jit
    def f(x):
      assert tracing_ok
      lst.append(1.0)
      lst.append({'a': 2.0})
      lst.append(x + 3.0)

    tracing_ok = True
    f(1)
    self.assertAllClose(lst._val, [1., {'a': 2.}, 4.])

    tracing_ok = False
    f(2)
    self.assertAllClose(lst.get(), [1., {'a': 2.}, 4., 1., {'a': 2.0}, 5.0])

  def test_jit_closure_nested(self):
    lst = List()

    @jax.jit
    def h(x):
      lst.append(x)

      @jax.jit
      def k(x):
        lst.append(x)

      k(1.0)
      k(2.0)

    h(0.0)
    self.assertAllClose(lst.get(), [0., 1., 2.])

  @parameterized.parameters([False, True])
  def test_scan_basic(self, jit):
    lst = List()

    def f():
      def body(_, x):
        lst.append(2 * x)
        lst.append(2 * x + 1)
        return (), ()
      (), () = jax.lax.scan(body, (), jnp.arange(3.))

    if jit:
      f = jax.jit(f)

    f()

    self.assertAllClose(lst.get(), [0., 1., 2., 3., 4., 5.])

  @parameterized.parameters([False, True])
  def test_scan_basic_hetero(self, jit):
    lst = List()

    def f():
      def body(_, x):
        lst.append(2 * x)
        lst.append({'a': (2 * x + 1, 2 * x + 2)})
        return (), ()
      (), () = jax.lax.scan(body, (), jnp.arange(3.))

    if jit:
      f = jax.jit(f)

    f()

    expected = [
        0.,
        {'a': (1., 2.)},
        2.,
        {'a': (3., 4.)},
        4.,
        {'a': (5., 6.)},
    ]
    self.assertAllClose(lst.get(), expected)

  @parameterized.parameters([False, True])
  def test_get_basic(self, jit):

    def f():
      lst = List()
      lst.append(1.)
      lst.append(2.)
      return lst.get()

    if jit:
      f = jax.jit(f)

    lst = f()
    self.assertAllClose(lst, [1., 2.])

  def test_freeze_nonlocal_list(self):
    lst = List()

    @jax.jit
    def f():
      lst.get()

    with self.assertRaisesRegex(Exception, "can't read the value"):
      f()

  def test_freeze_nonlocal_list_nested(self):
    @jax.jit
    def f():
      lst = List()

      @jax.jit
      def g():
        lst.get()

      g()

    with self.assertRaisesRegex(Exception, "can't read the value"):
      f()

  @parameterized.parameters([False, True])
  def test_append_after_get(self, jit):
    def f():
      lst = List()
      lst.append(1.)
      lst.append(2.)
      val = lst.get()
      lst.append(3.)
      return lst.get()

    if jit:
      f = jax.jit(f)

    lst = f()
    self.assertAllClose(lst, [1., 2., 3.])

  def test_get_on_nonlocal_list_closure(self):
    lst = List()

    @jax.jit
    def f():
      lst.append(1.)
      lst.append(2.)
      with self.assertRaisesRegex(Exception, "can't read"):
        val = lst.get()

  def test_get_on_nonlocal_list_arg(self):
    lst = List()

    @jax.jit
    def f(lst):
      lst.append(1.)
      lst.append(2.)
      with self.assertRaisesRegex(Exception, "can't read"):
        val = lst.get()

  @parameterized.parameters([False, True])
  def test_custom_vjp_plumbing(self, jit):
    lst = List()

    @jax.custom_vjp
    def foo(x):
      return x
    def foo_fwd(x):
      return foo(x), None
    def foo_bwd(_, g):
      lst.append(g)
      return g,
    foo.defvjp(foo_fwd, foo_bwd)

    def f(x):
      x = 2 * x
      x = foo(x)
      x = 2 * x
      return x

    if jit:
      f = jax.jit(f)

    jax.grad(f)(1.0)
    self.assertAllClose(lst.get(), [2.0])

  def test_error_passing_multiple_times_to_jit(self):
    @jax.jit
    def f(lst1, lst2):
      ...

    b = List([])
    with self.assertRaisesRegex(ValueError, "a List instance can't be passed"):
      f(b, b)


if __name__ == '__main__':
  absltest.main(testLoader=jtu.JaxTestLoader())
