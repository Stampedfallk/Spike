'''
-------------------------------------------------------------------------------
-- Title      : UART_tx runner
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : uart_tx_runner.py
-- Author     : Jere Nissinen
-- Edited     : 26.10.2026
-------------------------------------------------------------------------------
-- Description: Cocotb runner for building and simulating the uart_tx with GHDL.
-------------------------------------------------------------------------------
'''
from pathlib import Path
from cocotb_tools.runner import get_runner

def test_uart_tx_runner():

    project_dir = Path(__file__).resolve().parent.parent

    vhdl_sources = [
        project_dir / "vhd" /  "uart_tx.vhd",
    ]

    build_dir = project_dir / "sim_build"

    runner = get_runner("ghdl")

    runner.build(
        sources=vhdl_sources,
        hdl_toplevel="uart_tx",
        build_args=["--std=08"],
        build_dir=build_dir,
        always=True,
        waves=True,
    )

    runner.test(
        hdl_toplevel="uart_tx",
        test_module="test_uart_tx",
        build_dir=build_dir,
        test_args=["--std=08"],
        waves=True,
    )

if __name__ == "__main__":
    test_uart_tx_runner()