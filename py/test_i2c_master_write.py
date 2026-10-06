'''
-------------------------------------------------------------------------------
-- Title      : i2c master write test
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_master_write.py
-- Author     : Jere Nissinen
-- Edited     : 5.10.2026
-------------------------------------------------------------------------------
-- Description: A write test for the i2c_master. This test writes 1 address byte and 1 data byte
-- through the i2c_master and checks that it outputs them correctly.
-------------------------------------------------------------------------------
'''
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

@cocotb.test()
async def test_i2c_master_write(dut):

    #Send these 2 bytes in this test
    i2c_addr = 0x00
    addr_bits = [
        (i2c_addr >> bit) & 1
        for bit in range(7,-1,-1)
    ]
    i2c_data = 0x11
    data_bits = [
        (i2c_data >> bit) & 1
        for bit in range(7,-1,-1)
    ]

    #Generating the 10MHz clock and instantiating the other input ports
    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    dut.rst_n.value = 0
    dut.start_in.value = 0
    dut.end_in.value = 0
    dut.byte_in.value = 0

    dut.slave_sda_drive_low_in.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    #Lift reset and start measurement
    dut.rst_n.value = 1

    for _ in range(2):
        await RisingEdge(dut.clk)

    dut.start_in.value = 1
    dut.byte_in.value = i2c_addr
    await RisingEdge(dut.clk)
    dut.start_in.value = 0

    await FallingEdge(dut.sdat_out)

    received_bits = [0] * 8

    for i, bit in enumerate(addr_bits):
        dut._log.info(f"Waiting for SCLK rising edge {i}")

        await RisingEdge(dut.sclk_out)

        dut._log.info(f"SCLK rising edge {i} detected")
        received_bit = int(dut.sdat_out.value)
        dut._log.info(f"the received bit{received_bit}")
        received_bits[i] = received_bit

    assert received_bits == addr_bits, (
        f"Expected {addr_bits},"
        f"got {received_bits}"
    )
    #Sending ACK and checking that the byte_done works
    await FallingEdge(dut.sclk_out)
    dut.slave_sda_drive_low_in.value = 1
    dut._log.info(f"Address ACK asserted")

    await RisingEdge(dut.sclk_out)
    await RisingEdge(dut.byte_done_out)
    await FallingEdge(dut.sclk_out)

    dut.slave_sda_drive_low_in.value = 0

    dut._log.info(f"Address ACK released")

    #Once byte is done we can send the new value and tell the design that we are sending the last byte
    dut.byte_in.value = i2c_data
    dut.end_in.value = 1
    for i, bit in enumerate(data_bits):
        dut._log.info(f"Waiting for SCLK rising edge {i}")

        await RisingEdge(dut.sclk_out)

        dut._log.info(f"SCLK rising edge {i} detected")
        received_bit = int(dut.sdat_out.value)
        dut._log.info(f"the received bit{received_bit}")
        received_bits[i] = received_bit

    assert received_bits == data_bits, (
        f"Expected {data_bits},"
        f"got {received_bits}"
    )

    #Sending last ACK
    await FallingEdge(dut.sclk_out)

    dut.slave_sda_drive_low_in.value = 1

    dut._log.info("Data ACK asserted")

    await RisingEdge(dut.sclk_out)

    await FallingEdge(dut.sclk_out)

    dut.slave_sda_drive_low_in.value = 0
    dut.end_in.value = 0

    dut._log.info("Data ACK released")

    await RisingEdge(dut.sdat_out)

    dut._log.info("I2C write transaction completed")

    for _ in range(10):
        await RisingEdge(dut.clk)