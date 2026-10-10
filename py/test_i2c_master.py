'''
-------------------------------------------------------------------------------
-- Title      : i2c master write test
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_master.py
-- Author     : Jere Nissinen
-- Edited     : 10.10.2026
-------------------------------------------------------------------------------
-- Description: Containts the test sequences for the I2C_master
-------------------------------------------------------------------------------
'''
import random

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ValueChange

#Helper function for detecting i2c end condition.
async def wait_for_stop(dut):
    while True:
        await ValueChange(dut.sdat_out) #Check that end condition happens correctly
        sda = str(dut.sdat_out.value)
        scl = str(dut.sclk_out.value)
        if sda in ("1", "H") and scl in ("1", "H"):
            return

"""
Tests Sends 1 address byte and 1 data byte through the master.

Verifies:
- Address transmittion
- Data byte transmittion
- ACK handling
- Stop condition
"""
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

    while True:
        await ValueChange(dut.sdat_out)

        sda = str(dut.sdat_out.value)
        scl = str(dut.sclk_out.value)

        if sda in ("1", "H") and scl in ("1", "H"):
            dut._log.info("I2C STOP condition detected")
            break

    dut._log.info("I2C write transaction completed")

    for _ in range(10):
        await RisingEdge(dut.clk)



"""
Tests I2C write operation using randomized data.

Verifies:
- Multiple consecutive byte transfers
- Random data values
- ACK handling
- NACK handling and retransmission
"""
@cocotb.test()
async def test_i2c_master_random_write(dut):

    NUM_BYTES = 100

    #Start reference clock
    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    #Initial values¨
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

    #Generate random bytes
    test_bytes = [
        random.randint(0,225)
        for _ in range(NUM_BYTES)
    ]

    #First byte starts the I2C communication
    test_bytes[0] &= 0xFE
    dut.byte_in.value = test_bytes[0]
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    await FallingEdge(dut.sdat_out)

    byte_index = 0

    while byte_index < NUM_BYTES:

        expected = test_bytes[byte_index]

        received = 0

        #Receive one byte from the master
        for _ in range(8):

            await RisingEdge(dut.sclk_out)
            bit = int(dut.sdat_out.value)
            received = (received << 1) | bit

        dut._log.info(
            f"Byte {byte_index}: "
            f"expected=0x{expected:02X}, "
            f"receivedf=0x{received:02X}"
        )

        assert received == expected, (
            f"Byte {byte_index}: "
            f"expected=0x{expected:02X}, "
            f"receivedf=0x{received:02X}"            
        )

        #Randomly decide wheter slave responds ACK or NACK
        send_ack = random.random() < 0.8

        await FallingEdge(dut.sclk_out)

        if send_ack:
            dut.slave_sda_drive_low_in.value = 1
            dut._log.info(f"Byte {byte_index}: ACK")
        else:
            dut.slave_sda_drive_low_in.value = 0
            dut._log.info(f"Byte {byte_index}: NACK")

        #ACK/NACK clock
        await RisingEdge(dut.sclk_out)   
        await FallingEdge(dut.sclk_out)

        dut.slave_sda_drive_low_in.value = 0

        if send_ack:
            byte_index += 1

            if byte_index < NUM_BYTES:
                dut.byte_in.value = test_bytes[byte_index]

                if byte_index == NUM_BYTES-1:
                    dut.end_in.value = 1
        else:
            #Do not increment since a retransmittion is expected.
            dut._log.info(
                f"Expecting retransmittion of 0x{expected:02X}"
                f"byte index = {byte_index}"
                f"byte_in = 0x{int(dut.byte_in.value):02X}"
            )
    dut.end_in.value = 0

    dut._log.info(
        f"Succesfully transmitted {NUM_BYTES} randomized bytes"
    )  

"""
Tests a basic I2C read transaction.

Verifies:
- Read address transmission
- Address ACK
- Data reception
- Master NACK after the final byte
- STOP condition
"""
@cocotb.test()
async def test_i2c_master_read(dut):

    #Test values:

    #7-bit address + R bit
    i2c_addr = 0x81 #(10000001)

    #Slave sends this byte
    slave_data = 0xAA

    data_bits = [
        (slave_data >> bit) & 1
        for bit in range(7,-1,-1)
    ]

    cocotb.start_soon(Clock(dut.clk, 100, unit="ns").start())

    dut.rst_n.value = 0
    dut.start_in.value = 0
    dut.end_in.value = 0
    dut.byte_in.value = 0
    dut.slave_sda_drive_low_in.value = 0

    for _ in range(5):
        await RisingEdge(dut.clk)

    # Release reset
    dut.rst_n.value = 1
    for _ in range(2):
        await RisingEdge(dut.clk)    

    dut.byte_in.value = i2c_addr
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    await FallingEdge(dut.sdat_out)

    received_addr = 0

    for _ in range(8):
        await RisingEdge(dut.sclk_out)

        sda = str(dut.sdat_out.value)
        if sda in ("1", "H"):
            bit = 1
        else:
            bit = 0

        received_addr = (received_addr << 1) | bit

    dut._log.info(
        f"Address received from master: 0x{received_addr:02X}"
    )

    assert received_addr == i2c_addr, (
        f"Expected address 0x{i2c_addr:02X}, "
        f"got 0x{received_addr:02X}"
    )


    await FallingEdge(dut.sclk_out)

    # Pull SDA low

    dut.slave_sda_drive_low_in.value = 1

    dut._log.info("Slave ACK address")

    # ACK clock pulse

    await RisingEdge(dut.sclk_out)

    await FallingEdge(dut.sclk_out)
    # Release SDA again

    dut.slave_sda_drive_low_in.value = 0    

    #Receiving only one data byte
    dut.end_in.value = 1

    for i, bit in enumerate(data_bits):

        if bit == 0:
            dut.slave_sda_drive_low_in.value = 1
        else:
            dut.slave_sda_drive_low_in.value = 0

        dut._log.info(
            f"Sending bt {i}: {bit}"
        )

        #Dut should sample the bit here
        await RisingEdge(dut.sclk_out)
        await FallingEdge(dut.sclk_out)

    #Slave releases SDA after complete byte for master to send ack/nack (nack expected)
    dut.slave_sda_drive_low_in.value = 0

    assert int(dut.byte_out.value) == slave_data, (
        f"Expected master byte_out = 0x{slave_data:02X}, "
        f"got 0x{int(dut.byte_out.value):02X}"
    )

    dut._log.info(
    f"Master received 0x{int(dut.byte_out.value):02X}"
    )

    await RisingEdge(dut.sclk_out)

    sda = str(dut.sdat_out.value)

    dut._log.info(
        f"Master ACK/NACK bit: SDA={sda}"
    )

    assert sda in ("1", "H"), (
    f"Expected master NACK after final byte, "
    f"but SDA was {sda}"
    )

    await FallingEdge(dut.sclk_out)

    if dut.byte_done_out.value == 0:
        await RisingEdge(dut.byte_done_out)

    dut._log.info("byte_done_out detected")

    await wait_for_stop(dut)
    dut._log.info("I2C STOP detected")
    dut.end_in.value = 0
    dut._log.info(
    "I2C read test completed successfully"
    )


"""
Tests I2C read operation using randomized data.

Verifies:
- Address NACK handling and retransmission
- Multiple consecutive byte receptions
- Random data values
- Master ACK/NACK behavior
- STOP condition
"""
@cocotb.test()
async def test_i2c_master_read_random(dut):

    #Try to receive 10 bytes
    NUM_BYTES = 10

    #How many nacks we send before sending the ack
    NUM_NACKS = 4

    #Start reference clock
    cocotb.start_soon(
        Clock(dut.clk, 100, unit="ns").start()
    )

    #Initial values¨
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

    #Generate the random bytes This will be received by the master
    test_bytes = [
        random.randint(0,225)
        for _ in range(NUM_BYTES)
    ]

    #The deivece address
    i2c_addr = 0x81 #(10000001)

    dut.byte_in.value = i2c_addr
    dut.start_in.value = 1

    await RisingEdge(dut.clk)

    dut.start_in.value = 0

    await FallingEdge(dut.sdat_out)

    nack_index = 0

    while nack_index <= NUM_NACKS:

        received = 0
        for _ in range(8):
            await RisingEdge(dut.sclk_out)
            bit = int(dut.sdat_out.value)
            received = (received << 1) | bit

        dut._log.info(
            f"expected=0x{i2c_addr:02X}, "
            f"receivedf=0x{received:02X}"
        )

        assert received == i2c_addr, (
            f"expected=0x{i2c_addr:02X}, "
            f"receivedf=0x{received:02X}"            
        )

        #Send nack
        await FallingEdge(dut.sclk_out)

        #If the amount of nacks has been reached send ack
        if nack_index == NUM_NACKS:
            dut.slave_sda_drive_low_in.value = 1
            dut._log.info(f"Sending ACK")

        else:
            dut.slave_sda_drive_low_in.value = 0
            dut._log.info(f"Sending NACK: {nack_index}")

        await RisingEdge(dut.sclk_out)
        await FallingEdge(dut.sclk_out)

        dut.slave_sda_drive_low_in.value = 0

        nack_index += 1

    byte_index = 0


    #Sending the bytes
    while byte_index < NUM_BYTES:

        if byte_index == NUM_BYTES - 1:
            dut._log.info(f"Lifting end_in")
            dut.end_in.value = 1


        data_bits = [
            (test_bytes[byte_index] >> bit) & 1
            for bit in range(7,-1,-1)
        ]

        for i, bit in enumerate(data_bits):
            if bit == 0:
                dut.slave_sda_drive_low_in.value = 1
            else:
                dut.slave_sda_drive_low_in.value = 0

            await RisingEdge(dut.sclk_out)
            await FallingEdge(dut.sclk_out)

        #Releasing the sda for nack/ack
        dut.slave_sda_drive_low_in.value = 0

        assert int(dut.byte_out.value) == test_bytes[byte_index], (
            f"Expected master byte_out = 0x{test_bytes[byte_index]:02X}, "
            f"got 0x{int(dut.byte_out.value):02X}"
        )

        dut._log.info(
        f"Master received 0x{int(dut.byte_out.value):02X}"
        )

        await RisingEdge(dut.sclk_out)

        sda = str(dut.sdat_out.value)
        dut._log.info(
        f"Master ACK/NACK bit: SDA={sda}"
        )
        
        if byte_index < NUM_BYTES - 1:
            assert sda == "0", (
                f"Expected ACK after byte {byte_index}, got SDA={sda}"
            )
        else:
            assert sda in ("1", "H"), (
                f"Expected NACK after final byte, got SDA={sda}"
            )

        await FallingEdge(dut.sclk_out)

        byte_index += 1
        dut._log.info(f"byte index incremented. It is now {byte_index}")

    dut.end_in.value = 0

    await wait_for_stop(dut)
    dut._log.info("I2C STOP detected")
    dut.end_in.value = 0
    dut._log.info(
        "I2C read random data test completed succesfully"
    )



    