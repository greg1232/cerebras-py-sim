from .compiler.kernel import cs3_kernel, KernelArgs
from .driver.api import CS3Driver


@cs3_kernel(block_w=16, block_h=16)
def dummy_kernel(args):
    """A no-op kernel used to exercise the launch path."""
    pass


def main():
    driver = CS3Driver()

    n_floats = 1024
    size = n_floats * 4  # float32

    a = driver.cs3_malloc(size)
    b = driver.cs3_malloc(size)

    driver.cs3_launch(
        dummy_kernel,
        grid_w=1,
        grid_h=1,
        block_w=16,
        block_h=16,
        args=KernelArgs({"a": a, "b": b, "n": n_floats}).args,
    )

    driver.cs3_sync()

    commands = driver.queue.drain()
    print(f"CS3 Simulator: Queue drained, {len(commands)} commands processed")


if __name__ == "__main__":
    main()
