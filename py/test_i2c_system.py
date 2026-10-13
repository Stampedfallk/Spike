'''
-------------------------------------------------------------------------------
-- Title      : i2c system tests
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_system.py
-- Author     : Jere Nissinen
-- Edited     : 13.10.2026
-------------------------------------------------------------------------------
-- Description: Containts the test sequences and helper functions for the I2C_system
-------------------------------------------------------------------------------
'''
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ValueChange

#Helper functions:

#Detect i2c start condition
async def wait_for_start(dut):
    while True:
        await FallingEdge(dut.sdat_out)
        if dut.sclk_out.value == 1:
            return

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

#Sending a nack
async def send_nack(dut):
    #Wait until sclk goes down
    await FallingEdge(dut.sclk_out)
    dut.slave_sda_drive_low_in.value = 0

    #Nack cycle
    await RisingEdge(dut.sclk_out)
    await FallingEdge(dut.sclk_out)

#Send one byte from slave to master
async def send_i2c_byte(dut, data):
    for bit_index in range(7,-1,-1):

        bit = (data >> bit_index) & 1

        if bit == 0:
            dut.slave_sda_drive_low_in.value = 1
        else:
            dut.slave_sda_drive_low_in.value = 0

        await RisingEdge(dut.sclk_out)
        await FallingEdge(dut.sclk_out)

    #Release sda so master can send ack/nack.
    dut.slave_sda_drive_low_in.value = 0
    #ack/nack cycle
    await RisingEdge(dut.sclk_out)
    await FallingEdge(dut.sclk_out)

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

'''
Tests HYGRO temperature and humidity measurement

Verifies:
- Measurement starts after trigger
- Correct HYGRO write address and measurement registers are transmitted
- Sensor can respond with NACK while measurement is not ready
- Controller retries reading until sensor responds with NACK
- Temperature output contains the correct 16-bit value
- Humidity output containts the correct 16-bit value
- Transaction ends with STOP condition
'''
@cocotb.test()
async def test_hygro_measurement(dut):

    temperature = 0x1234
    humidity = 0x5678

    #Start clock
    cocotb.start_soon(
        Clock(dut.clk, 100, unit = "ns").start()
    )

    dut.trigger_hygro_measurement.value = 0
    dut.slave_sda_drive_low_in.value = 0

    #Trigger measurement
    dut.trigger_hygro_measurement.value = 1
    await RisingEdge(dut.clk)
    dut.trigger_hygro_measurement.value = 0

    dut._log.info("Hygro measurement triggered")

    #Measurement request:
    # START
    # 0x80 -> ACK
    # 0x00 -> ACK
    # STOP

    await wait_for_start(dut)
    await receive_and_check_byte(dut, 0x80)
    await receive_and_check_byte(dut, 0x00)
    await wait_for_stop(dut)

    dut._log.info("Measurement request received")

    #Sensor busy
    # Controller tries to read with 0x81
    # Sensor resonds with nack 3 times
    
    await wait_for_start(dut)
    for attempt in range(3):
        received = await receive_i2c_byte(dut)

        assert received == 0x81, (
            f"Expected I2C byte 0x81, "
            f"fot 0x{received:02X}"
        )

        dut._log.info(
            f"Read attempt {attempt + 1}: sensor busy -> NACK"
        )

        await send_nack(dut)

    #Sensor ready
    # 4th 0x81 gets ACK
    await receive_and_check_byte(dut, 0x81)

    dut._log.info("Read attempt 4: sensor ready -> ACK")

    #Send temperature and humidity
    temperature_msb = (temperature >> 8) & 0xFF
    temperature_lsb = temperature & 0xFF

    humidity_msb = (humidity >> 8) & 0xFF
    humidity_lsb = humidity & 0xFF

    await send_i2c_byte(dut, temperature_msb)
    await send_i2c_byte(dut, temperature_lsb)
    await send_i2c_byte(dut, humidity_msb)
    await send_i2c_byte(dut, humidity_lsb)
    await wait_for_stop(dut)

    temperature_received = int(dut.temperature_out.value)
    humidity_received = int(dut.humidity_out.value)

    dut._log.info(
    f"Temperature expected: 0x{temperature:04X}, "
    f"received: 0x{temperature_received:04X}"
    )

    dut._log.info(
    f"Humidity expected: 0x{humidity:04X}, "
    f"received: 0x{humidity_received:04X}"
    )

    assert temperature_received == temperature, (
    f"Expected temperature 0x{temperature:04X}, "
    f"got 0x{temperature_received:04X}"
    )

    assert humidity_received == humidity, (
    f"Expected humidity 0x{humidity:04X}, "
    f"got 0x{humidity_received:04X}"
    )

    dut._log.info(
    "HYGRO measurement test passed"
    )    