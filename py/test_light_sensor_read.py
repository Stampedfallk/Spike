'''
-------------------------------------------------------------------------------
-- Title      : Light sensor read test
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_light_sensor_read.py
-- Author     : Jere Nissinen
-- Edited     : 2.10.2026
-------------------------------------------------------------------------------
-- Description: Verifies the light sensor controller by emulating ADC serial data and
-- checking that the received measurement is correct.
-------------------------------------------------------------------------------
'''
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_light_sensor_read(dut):

    #Generating the 10MHz clock and instantiating the other input ports
    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    dut.rst_n.value = 0
    dut.trigger_measurement_in.value = 0
    dut.sdata_in.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    #Lift reset and start measurement
    dut.rst_n.value = 1

    for _ in range(2):
        await RisingEdge(dut.clk)

    dut.trigger_measurement_in.value = 1
    await RisingEdge(dut.clk)
    dut.trigger_measurement_in.value = 0 

    await FallingEdge(dut.cs_out)

    #Send this value to the DUT and verify that it got it correctly.
    adc_value = 0xB5

    data_bits = [
        (adc_value >> bit) & 1
        for bit in range(7,-1,-1)
    ]

    adc_bits = [
        0, 0, 0,
        *data_bits,
        0, 0, 0, 0
    ]

    for i, bit in enumerate(adc_bits):
        dut._log.info(f"Waiting for SCLK falling edge {i}")

        await FallingEdge(dut.sclk_out)

        dut._log.info(f"SCLK falling edge {i} detected")
        dut.sdata_in.value = bit

    await RisingEdge(dut.cs_out)

    await RisingEdge(dut.clk)
    received = int(dut.data_out.value)

    assert received == adc_value, (
        f"Expected 0x{adc_value:02X},"
        f"got 0x{received:02X}"
    )

    dut._log.info(
        f"ADC measurement succesful: 0x{received:02X}"
    )