'''
-------------------------------------------------------------------------------
-- Title      : I2C_arbitter runner
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_arbitter_runner.py
-- Author     : Jere Nissinen
-- Edited     : 11.10.2026
-------------------------------------------------------------------------------
-- Description: Cocotb runner for building and simulating the i2c_arbitter with GHDL.
-------------------------------------------------------------------------------
'''
from pathlib import Path
from cocotb_tools.runner import get_runner

def test_i2c_arbitter_runner():

    project_dir = Path(__file__).resolve().parent.parent

    vhdl_sources = [
        project_dir / "vhd" /  "i2c_arbitter.vhd",
    ]

    build_dir = project_dir / "sim_build"

    runner = get_runner("ghdl")

    runner.build(
        sources=vhdl_sources,
        hdl_toplevel="i2c_arbitter",
        build_args=["--std=08"],
        build_dir=build_dir,
        always=True,
        waves=True,
    )

    runner.test(
        hdl_toplevel="i2c_arbitter",
        test_module="test_i2c_arbitter",
        build_dir=build_dir,
        test_args=["--std=08"],
        waves=True,
    )

if __name__ == "__main__":
    test_i2c_arbitter_runner()