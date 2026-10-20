'''
-------------------------------------------------------------------------------
-- Title      : i2c master tests
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_master.py
-- Author     : Jere Nissinen
-- Edited     : 20.10.2026
-------------------------------------------------------------------------------
-- Description: Containts the test sequences for the I2C_master
-------------------------------------------------------------------------------
'''
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ValueChange


# Helper functions

# Detect I2C start condition
async def wait_for_start(dut):
    while True:
        await FallingEdge(dut.sdat_out)

        scl = str(dut.sclk_out.value)

        if scl in ("1", "H"):
            return


# Detect I2C stop condition
async def wait_for_stop(dut):
    while True:
        await ValueChange(dut.sdat_out)

        sda = str(dut.sdat_out.value)
        scl = str(dut.sclk_out.value)

        if sda in ("1", "H") and scl in ("1", "H"):
            return


# Convert resolved SDA value to binary value
def read_sda(dut):
    sda = str(dut.sdat_out.value)

    if sda in ("1", "H"):
        return 1

    return 0


# Receive one byte transmitted by the I2C master
async def receive_i2c_byte(dut):
    received = 0

    for _ in range(8):
        await RisingEdge(dut.sclk_out)

        bit = read_sda(dut)

        received = (received << 1) | bit

    return received


# Check one byte transmitted by the I2C master
async def receive_and_check_byte(dut, expected):
    received = await receive_i2c_byte(dut)

    dut._log.info(
        f"Expected 0x{expected:02X}, "
        f"received 0x{received:02X}"
    )

    assert received == expected, (
        f"Expected I2C byte 0x{expected:02X}, "
        f"got 0x{received:02X}"
    )

    return received

# Send ack to the I2C master
async def send_ack(dut):
    await FallingEdge(dut.sclk_out)

    # ACK = pull SDA low
    dut.slave_sda_drive_low_in.value = 1

    await RisingEdge(dut.sclk_out)

    # Wait until master has actually processed ACK
    await RisingEdge(dut.byte_done_out)

    assert int(dut.ack_out.value) == 0, (
        "Master reported NACK even though slave sent ACK"
    )

    # Finish ACK clock
    await FallingEdge(dut.sclk_out)

    # Release SDA
    dut.slave_sda_drive_low_in.value = 0

# Send nack to the I2C master
async def send_nack(dut):
    dut._log.info(
        f"send_nack entered: "
        f"SCL={dut.sclk_out.value}, "
        f"SDA={dut.sdat_out.value}"
    )

    # Wait until SCL goes low after address byte
    await FallingEdge(dut.sclk_out)

    dut._log.info(
        "Falling edge before NACK detected"
    )

    # NACK = release SDA
    dut.slave_sda_drive_low_in.value = 0

    # Wait for ACK/NACK clock
    await RisingEdge(dut.sclk_out)

    dut._log.info(
        f"NACK on bus: SDA={dut.sdat_out.value}"
    )

    # Master samples ACK/NACK internally later
    # during the SCL high phase.
    await RisingEdge(dut.byte_done_out)

    dut._log.info(
        f"Master processed NACK: "
        f"ack_out={dut.ack_out.value}"
    )

    assert int(dut.ack_out.value) == 1, (
        "Master did not report NACK"
    )


# Send one byte from slave to master
async def send_i2c_byte(dut, data):
    for bit_index in range(7, -1, -1):

        bit = (data >> bit_index) & 1

        if bit == 0:
            dut.slave_sda_drive_low_in.value = 1
        else:
            dut.slave_sda_drive_low_in.value = 0

        await RisingEdge(dut.sclk_out)
        await FallingEdge(dut.sclk_out)

    # Release SDA for master's ACK/NACK
    dut.slave_sda_drive_low_in.value = 0


# Reset DUT
async def reset_dut(dut):
    dut.rst_n.value = 0
    dut.start_in.value = 0
    dut.end_in.value = 0
    dut.byte_in.value = 0
    dut.slave_sda_drive_low_in.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    for _ in range(2):
        await RisingEdge(dut.clk)


# Start an I2C transaction
async def start_transaction(dut, first_byte):
    dut.byte_in.value = first_byte
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    await wait_for_start(dut)

# Tests

"""
Tests sending one address byte and one data byte through the master.

Verifies:
- Address transmission
- Data byte transmission
- ACK handling
- ack_out remains low on ACK
- STOP condition
"""
@cocotb.test()
async def test_i2c_master_write(dut):

    i2c_addr = 0x00
    i2c_data = 0x11

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    await reset_dut(dut)

    # Address

    await start_transaction(dut, i2c_addr)

    await receive_and_check_byte(
        dut,
        i2c_addr
    )

    await send_ack(dut)

    dut._log.info("Address ACK completed")

    # Data

    dut.byte_in.value = i2c_data
    dut.end_in.value = 1

    await receive_and_check_byte(
        dut,
        i2c_data
    )

    await send_ack(dut)

    dut._log.info("Data ACK completed")

    # STOP

    await wait_for_stop(dut)

    dut.end_in.value = 0

    dut._log.info(
        "I2C write transaction completed"
    )


"""
Tests randomized I2C write operation.

Verifies:
- Multiple consecutive byte transfers
- Random 8-bit data values
- ACK handling
- Correct byte ordering
- STOP condition
"""
@cocotb.test()
async def test_i2c_master_random_write(dut):

    NUM_BYTES = 100

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    await reset_dut(dut)

    test_bytes = [
        random.randint(0, 255)
        for _ in range(NUM_BYTES)
    ]

    # First byte is interpreted as address.
    # Force write bit = 0.
    test_bytes[0] &= 0xFE

    await start_transaction(
        dut,
        test_bytes[0]
    )

    for byte_index in range(NUM_BYTES):

        expected = test_bytes[byte_index]

        await receive_and_check_byte(
            dut,
            expected
        )

        if byte_index == NUM_BYTES - 1:
            dut.end_in.value = 1

        await send_ack(dut)

        dut._log.info(
            f"Byte {byte_index}: "
            f"0x{expected:02X} transmitted successfully"
        )

        if byte_index < NUM_BYTES - 1:
            dut.byte_in.value = test_bytes[byte_index + 1]

    await wait_for_stop(dut)

    dut.end_in.value = 0

    dut._log.info(
        f"Successfully transmitted "
        f"{NUM_BYTES} randomized bytes"
    )


"""
Tests I2C NACK handling.

Verifies:
- Address transmission
- NACK detection
- ack_out goes high on NACK
- byte_done_out indicates completed address attempt
- Master generates STOP after NACK
- Master does not automatically retransmit
"""
@cocotb.test()
async def test_i2c_master_nack(dut):

    i2c_addr = 0x6D

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    await reset_dut(dut)

    await start_transaction(
        dut,
        i2c_addr
    )

    await receive_and_check_byte(
        dut,
        i2c_addr
    )

    dut._log.info(
        "Sending NACK to address 0x6D"
    )

    await send_nack(dut)

    assert int(dut.ack_out.value) == 1, (
        "Expected ack_out = 1 after NACK"
    )

    await wait_for_stop(dut)

    dut._log.info(
        "Master correctly generated STOP after NACK"
    )


"""
Tests repeated address attempts after NACK.

Verifies:
- Each retry starts a completely new I2C transaction
- NACK causes STOP
- Master does not automatically retransmit
- Controller/testbench can initiate a new retry
- Final ACK allows communication to continue
"""
@cocotb.test()
async def test_i2c_master_nack_retry(dut):

    i2c_addr = 0x6D
    NUM_NACKS = 4

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    await reset_dut(dut)

    # ---------------------------------------------------------
    # Four separate NACKed attempts
    # ---------------------------------------------------------

    for attempt in range(NUM_NACKS):

        await start_transaction(
            dut,
            i2c_addr
        )

        await receive_and_check_byte(
            dut,
            i2c_addr
        )

        dut._log.info(
            f"Attempt {attempt + 1}: NACK"
        )

        await send_nack(dut)

        assert int(dut.ack_out.value) == 1, (
            f"NACK not reported on attempt "
            f"{attempt + 1}"
        )

        await wait_for_stop(dut)

    # ---------------------------------------------------------
    # Fifth attempt receives ACK
    # ---------------------------------------------------------

    await start_transaction(
        dut,
        i2c_addr
    )

    await receive_and_check_byte(
        dut,
        i2c_addr
    )

    dut._log.info(
        "Final attempt: ACK"
    )

    await send_ack(dut)

    assert int(dut.ack_out.value) == 0, (
        "ack_out did not clear on successful transaction"
    )

    dut._log.info(
        "NACK retry test completed successfully"
    )


"""
Tests a basic I2C read transaction.

Verifies:
- Read address transmission
- Address ACK
- Data reception
- Master NACK after final byte
- STOP condition
"""
@cocotb.test()
async def test_i2c_master_read(dut):

    i2c_addr = 0x81
    slave_data = 0xAA

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    await reset_dut(dut)

    # ---------------------------------------------------------
    # Read address
    # ---------------------------------------------------------

    await start_transaction(
        dut,
        i2c_addr
    )

    await receive_and_check_byte(
        dut,
        i2c_addr
    )

    await send_ack(dut)

    # ---------------------------------------------------------
    # Receive one byte
    # ---------------------------------------------------------

    dut.end_in.value = 1

    await send_i2c_byte(
        dut,
        slave_data
    )

    assert int(dut.byte_out.value) == slave_data, (
        f"Expected master byte_out = 0x{slave_data:02X}, "
        f"got 0x{int(dut.byte_out.value):02X}"
    )

    dut._log.info(
        f"Master received "
        f"0x{int(dut.byte_out.value):02X}"
    )

    # ---------------------------------------------------------
    # Master should NACK final received byte
    # ---------------------------------------------------------

    await RisingEdge(dut.sclk_out)

    sda = str(dut.sdat_out.value)

    assert sda in ("1", "H"), (
        f"Expected master NACK after final byte, "
        f"got SDA={sda}"
    )

    await FallingEdge(dut.sclk_out)

    if dut.byte_done_out.value == 0:
        await RisingEdge(dut.byte_done_out)

    await wait_for_stop(dut)

    dut.end_in.value = 0

    dut._log.info(
        "I2C read test completed successfully"
    )


"""
Tests randomized multi-byte I2C read operation.

Verifies:
- Read address transmission
- Multiple consecutive byte receptions
- Random 8-bit data values
- Master ACK after intermediate bytes
- Master NACK after final byte
- STOP condition
"""
@cocotb.test()
async def test_i2c_master_read_random(dut):

    NUM_BYTES = 10

    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    await reset_dut(dut)

    test_bytes = [
        random.randint(0, 255)
        for _ in range(NUM_BYTES)
    ]

    i2c_addr = 0x81

    # Read address

    await start_transaction(
        dut,
        i2c_addr
    )

    await receive_and_check_byte(
        dut,
        i2c_addr
    )

    await send_ack(dut)

    # Sensor data

    for byte_index in range(NUM_BYTES):

        if byte_index == NUM_BYTES - 1:
            dut.end_in.value = 1

        expected = test_bytes[byte_index]

        await send_i2c_byte(
            dut,
            expected
        )

        received = int(dut.byte_out.value)

        assert received == expected, (
            f"Byte {byte_index}: "
            f"expected 0x{expected:02X}, "
            f"got 0x{received:02X}"
        )

        dut._log.info(
            f"Master received byte {byte_index}: "
            f"0x{received:02X}"
        )

        # Master ACK/NACK cycle
        await RisingEdge(dut.sclk_out)

        sda = str(dut.sdat_out.value)

        if byte_index < NUM_BYTES - 1:

            assert sda == "0", (
                f"Expected ACK after byte "
                f"{byte_index}, got SDA={sda}"
            )

        else:

            assert sda in ("1", "H"), (
                f"Expected NACK after final byte, "
                f"got SDA={sda}"
            )

        await FallingEdge(dut.sclk_out)

    dut.end_in.value = 0

    await wait_for_stop(dut)

    dut._log.info(
        "Random I2C read test completed successfully"
    )