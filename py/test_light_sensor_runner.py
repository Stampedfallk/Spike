'''
-------------------------------------------------------------------------------
-- Title      : Light sensor runner
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_light_sensor_runner.py
-- Author     : Jere Nissinen
-- Edited     : 2.10.2026
-------------------------------------------------------------------------------
-- Description: Cocotb runner for building and simulating the light sensor controller with
-- GHDL.
-------------------------------------------------------------------------------
'''
from pathlib import Path
from cocotb_tools.runner import get_runner

def test_light_sensor_runner():

    project_dir = Path(__file__).resolve().parent.parent

    vhdl_sources = [
        project_dir / "vhd" /  "light_sensor_ctrl.vhd"
    ]

    build_dir = project_dir / "sim_build"

    runner = get_runner("ghdl")

    runner.build(
        sources=vhdl_sources,
        hdl_toplevel="light_sensor_ctrl",
        build_args=["--std=08"],
        build_dir=build_dir,
        always=True,
        waves=True,
    )

    runner.test(
        hdl_toplevel="light_sensor_ctrl",
        test_module="test_light_sensor_read",
        build_dir=build_dir,
        test_args=["--std=08"],
        waves=True,
    )

if __name__ == "__main__":
    test_light_sensor_runner()