import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.compiler.kernel import cs3_kernel, Kernel, KernelArgs


class TestKernelDecorator(unittest.TestCase):
    def test_bare_decorator_returns_kernel(self):
        @cs3_kernel
        def saxpy(args):
            pass

        self.assertIsInstance(saxpy, Kernel)
        self.assertEqual(saxpy.name, 'saxpy')

    def test_decorator_with_block_dims(self):
        @cs3_kernel(block_w=16, block_h=8)
        def gemm(args):
            pass

        self.assertIsInstance(gemm, Kernel)
        self.assertEqual(gemm.block_w, 16)
        self.assertEqual(gemm.block_h, 8)

    def test_default_block_dims(self):
        @cs3_kernel
        def noop(args):
            pass

        self.assertEqual(noop.block_w, 1)
        self.assertEqual(noop.block_h, 1)

    def test_kernel_is_callable(self):
        """Kernel.__call__ passes through to the wrapped function."""
        results = []

        @cs3_kernel(block_w=4, block_h=4)
        def record(args):
            results.append(args['value'])

        record({'value': 42})
        self.assertEqual(results, [42])

    def test_kernel_name_preserved(self):
        @cs3_kernel(block_w=2, block_h=2)
        def heat_eq(args):
            pass

        self.assertEqual(heat_eq.name, 'heat_eq')


class TestKernelArgs(unittest.TestCase):
    def test_setitem_getitem(self):
        ka = KernelArgs()
        ka['alpha'] = 2.0
        self.assertEqual(ka['alpha'], 2.0)

    def test_missing_key_raises(self):
        ka = KernelArgs()
        with self.assertRaises(KeyError):
            _ = ka['missing']

    def test_init_with_dict(self):
        ka = KernelArgs(args={'n': 128, 'alpha': 1.0})
        self.assertEqual(ka['n'], 128)
        self.assertEqual(ka['alpha'], 1.0)


if __name__ == '__main__':
    unittest.main()
