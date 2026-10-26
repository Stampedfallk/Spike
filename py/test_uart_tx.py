'''
-------------------------------------------------------------------------------
-- Title      : UART TX tests
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_uart_tx.py
-- Author     : Jere Nissinen
-- Edited     : 26.10.2026
-------------------------------------------------------------------------------
-- Description: Contains the test sequences and helper functions for uart_tx
-------------------------------------------------------------------------------
'''
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


# Helper functions:

# Calculate baud divider from DUT generics
def get_baud_cycles():
    return int(125000000 / 115200)


# Wait one UART bit period
async def wait_uart_bit(dut):
    for _ in range(get_baud_cycles()):
        await RisingEdge(dut.clk)


# Receive one UART frame
async def receive_uart_byte(dut):

    baud_cycles = get_baud_cycles()

    # Wait for start bit
    while int(dut.tx_out.value) == 1:
        await RisingEdge(dut.clk)

    # Move close to middle of first data bit
    for _ in range(int(baud_cycles * 1.5)):
        await RisingEdge(dut.clk)

    received = 0

    for bit_index in range(8):

        bit = int(dut.tx_out.value)

        received |= (bit << bit_index)

        for _ in range(baud_cycles):
            await RisingEdge(dut.clk)

    return received


# Tests:


"""
Tests UART idle state.

Verifies:
- TX line remains high after reset
- Busy signal remains low
"""
@cocotb.test()
async def test_uart_idle(dut):

    cocotb.start_soon(
        Clock(dut.clk, 8, unit="ns").start()
    )

    dut.rst_n.value = 0
    dut.start_in.value = 0
    dut.data_in.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    for _ in range(10):
        await RisingEdge(dut.clk)

    assert int(dut.tx_out.value) == 1, (
        "TX line should be idle high"
    )

    assert int(dut.busy_out.value) == 0, (
        "busy_out should be low in idle"
    )

    dut._log.info(
        "UART idle test passed"
    )


"""
Tests UART start bit generation.

Verifies:
- Transmission starts after start_in pulse
- Busy signal becomes high
- Start bit is driven low
"""
@cocotb.test()
async def test_uart_start_bit(dut):

    cocotb.start_soon(
        Clock(dut.clk, 8, unit="ns").start()
    )

    dut.rst_n.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    dut.data_in.value = 0x55
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    assert int(dut.busy_out.value) == 1, (
        "busy_out should be high during transmission"
    )

    assert int(dut.tx_out.value) == 0, (
        "Start bit should be low"
    )

    dut._log.info(
        "UART start bit test passed"
    )


"""
Tests UART transmission of one byte.

Verifies:
- Correct start bit
- Correct LSB-first transmission
- Correct received byte value
"""
@cocotb.test()
async def test_uart_single_byte(dut):

    TEST_BYTE = 0x55

    cocotb.start_soon(
        Clock(dut.clk, 8, unit="ns").start()
    )

    dut.rst_n.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    dut.data_in.value = TEST_BYTE
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    received = await receive_uart_byte(dut)

    dut._log.info(
        f"Expected 0x{TEST_BYTE:02X}, "
        f"received 0x{received:02X}"
    )

    assert received == TEST_BYTE, (
        f"Expected UART byte 0x{TEST_BYTE:02X}, "
        f"got 0x{received:02X}"
    )

    dut._log.info(
        "UART single byte test passed"
    )


"""
Tests UART stop bit and return to idle.

Verifies:
- Stop bit is high
- Transmission returns to idle
- Busy signal returns low
"""
@cocotb.test()
async def test_uart_stop_bit(dut):

    cocotb.start_soon(
        Clock(dut.clk, 8, unit="ns").start()
    )

    dut.rst_n.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    dut.data_in.value = 0xAA
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    # Wait long enough for whole frame
    baud_cycles = get_baud_cycles()

    for _ in range(12 * baud_cycles):
        await RisingEdge(dut.clk)

    assert int(dut.tx_out.value) == 1, (
        "TX line should be high after stop bit"
    )

    assert int(dut.busy_out.value) == 0, (
        "busy_out should return low after transmission"
    )

    dut._log.info(
        "UART stop bit test passed"
    )
