'''
-------------------------------------------------------------------------------
-- Title      : I2C_master runner
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_runner.py
-- Author     : Jere Nissinen
-- Edited     : 5.10.2026
-------------------------------------------------------------------------------
-- Description: Cocotb runner for building and simulating the i2c_master with GHDL.
-------------------------------------------------------------------------------
'''
from pathlib import Path
from cocotb_tools.runner import get_runner

def test_i2c_master_runner():

    project_dir = Path(__file__).resolve().parent.parent

    vhdl_sources = [
        project_dir / "vhd" /  "i2c_master.vhd",
        project_dir / "vhd" / "i2c_master_tb_wrapper.vhd"
    ]

    build_dir = project_dir / "sim_build"

    runner = get_runner("ghdl")

    runner.build(
        sources=vhdl_sources,
        hdl_toplevel="i2c_master_tb_wrapper",
        build_args=["--std=08"],
        build_dir=build_dir,
        always=True,
        waves=True,
    )

    runner.test(
        hdl_toplevel="i2c_master_tb_wrapper",
        test_module="test_i2c_master_write",
        build_dir=build_dir,
        test_args=["--std=08"],
        waves=True,
    )

if __name__ == "__main__":
    test_i2c_master_runner()