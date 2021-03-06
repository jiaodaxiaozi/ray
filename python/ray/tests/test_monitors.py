from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import multiprocessing
import os
import pytest
import subprocess
import time

import ray


def _test_cleanup_on_driver_exit(num_redis_shards):
    output = ray.utils.decode(
        subprocess.check_output(
            [
                "ray",
                "start",
                "--head",
                "--num-redis-shards",
                str(num_redis_shards),
            ],
            stderr=subprocess.STDOUT))
    lines = [m.strip() for m in output.split("\n")]
    init_cmd = [m for m in lines if m.startswith("ray.init")]
    assert 1 == len(init_cmd)
    address = init_cmd[0].split("address=\"")[-1][:-2]
    max_attempts_before_failing = 100
    # Wait for monitor.py to start working.
    time.sleep(2)

    def StateSummary():
        obj_tbl_len = len(ray.objects())
        task_tbl_len = len(ray.tasks())
        return obj_tbl_len, task_tbl_len

    def Driver(success):
        success.value = True
        # Start driver.
        ray.init(address=address)
        summary_start = StateSummary()
        if (0, 1) != summary_start:
            success.value = False

        # Two new objects.
        ray.get(ray.put(1111))
        ray.get(ray.put(1111))

        @ray.remote
        def f():
            ray.put(1111)  # Yet another object.
            return 1111  # A returned object as well.

        # 1 new function.
        attempts = 0
        while (2, 1) != StateSummary():
            time.sleep(0.1)
            attempts += 1
            if attempts == max_attempts_before_failing:
                success.value = False
                break

        ray.get(f.remote())
        attempts = 0
        while (4, 2) != StateSummary():
            time.sleep(0.1)
            attempts += 1
            if attempts == max_attempts_before_failing:
                success.value = False
                break

        ray.shutdown()

    success = multiprocessing.Value("b", False)
    driver = multiprocessing.Process(target=Driver, args=(success, ))
    driver.start()
    # Wait for client to exit.
    driver.join()

    # Just make sure Driver() is run and succeeded.
    assert success.value
    # Check that objects, tasks, and functions are cleaned up.
    ray.init(address=address)
    attempts = 0
    while (0, 1) != StateSummary():
        time.sleep(0.1)
        attempts += 1
        if attempts == max_attempts_before_failing:
            break
    assert (0, 1) == StateSummary()

    ray.shutdown()
    subprocess.check_output(["ray", "stop"])


@pytest.mark.skipif(
    os.environ.get("RAY_USE_NEW_GCS") == "on",
    reason="Hanging with the new GCS API.")
def test_cleanup_on_driver_exit_single_redis_shard():
    _test_cleanup_on_driver_exit(num_redis_shards=1)


@pytest.mark.skipif(
    os.environ.get("RAY_USE_NEW_GCS") == "on",
    reason="Hanging with the new GCS API.")
def test_cleanup_on_driver_exit_many_redis_shards():
    _test_cleanup_on_driver_exit(num_redis_shards=5)
    _test_cleanup_on_driver_exit(num_redis_shards=31)


if __name__ == "__main__":
    import pytest
    import sys
    # Make subprocess happy in bazel.
    os.environ["LC_ALL"] = "en_US.UTF-8"
    os.environ["LANG"] = "en_US.UTF-8"
    sys.exit(pytest.main(["-v", __file__]))
