'''
-------------------------------------------------------------------------------
-- Title      : i2c system tests
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_system.py
-- Author     : Jere Nissinen
-- Edited     : 12.10.2026
-------------------------------------------------------------------------------
-- Description: Containts the test sequences and helper functions for the I2C_system
-------------------------------------------------------------------------------
'''
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ValueChange

#Helper functions:

#Detect i2c stop condition
async def wait_for_stop(dut):
    while True:
        await ValueChange(dut.sdat_out)
        sda = str(dut.sdat_out.value)
        scl = str(dut.sclk_out.value)

        if sda in ("1", "H") and scl in ("1", "H"):
            return

#Receive byte through i2c and return it
async def receive_i2c_byte(dut):
    received = 0
    for _ in range(8):
        await RisingEdge(dut.sclk_out)
        sda = str(dut.sdat_out.value)

        if sda in ("1", "H"):
            bit = 1
        else:
            bit = 0

        received = (received << 1) | bit

    return received

#Sending an ack
async def send_ack(dut):
    #Wait until slck goes down before pulling sdat low
    await FallingEdge(dut.sclk_out)
    dut.slave_sda_drive_low_in.value = 1

    #Ack cycle
    await RisingEdge(dut.sclk_out)
    await FallingEdge(dut.sclk_out)

    #Release sdat
    dut.slave_sda_drive_low_in.value = 0

#Receive a byte and check correctness
async def receive_and_check_byte(dut, expected):
    received = await receive_i2c_byte(dut)

    dut._log.info(
        f"Expected 0x{expected:02X},"
        f"received 0x{received:02X}"
    )

    assert received == expected, (
        f"Expected I2C byte 0x{expected:02X}, "
        f"got 0x{received:02X}"        
    )

    await send_ack(dut)

#Tests:

"""
Tests automatic HYGRO configuration after reset.

Verifies:
- I2C communication starts after reset
- Correct HYGRO address is transmitted
- Correcvt configuration bytes are transmitted
- Slave ACKs each transmitted byte
- Transaction ends with STOP condition
"""
@cocotb.test()
async def test_hygro_configuration(dut):
    #Bytes that should be received
    HYGRO_WRITE_ADDR = 0x80
    HYGRO_CONFIG_REG = 0x02
    EXPECTED_CONFIG = [
        0x10,
        0x00
    ]

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    #Initial values
    dut.rst_n.value = 0
    dut.slave_sda_drive_low_in.value = 0

    #Keep reset high gor a couple of cycles
    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1
    dut._log.info("Reset released")

    await FallingEdge(dut.sdat_out)
    dut._log.info("I2C START detected")

    #Hygro address + write bit
    await receive_and_check_byte(
        dut,
        HYGRO_WRITE_ADDR
    )

    #Configuration register address
    await receive_and_check_byte(
        dut,
        HYGRO_CONFIG_REG
    )

    #Configuration data
    for expected_byte in EXPECTED_CONFIG:
        await receive_and_check_byte(
            dut,
            expected_byte
        )

    #Wait for stop condition
    await wait_for_stop(dut)

    dut._log.info("I2C STOP detected")

    dut._log.info("HYGRO configuration completed succesfully")