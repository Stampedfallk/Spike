'''
-------------------------------------------------------------------------------
-- Title      : i2c arbitter tests
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : test_i2c_arbitter.py
-- Author     : Jere Nissinen
-- Edited     : 11.10.2026
-------------------------------------------------------------------------------
-- Description: Contains the test sequences for the I2C_arbitter
-------------------------------------------------------------------------------
'''

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge


CLOCK_PERIOD = 10


#Helper functions:

#Reset the dut
async def reset_dut(dut):
    dut.requests_in.value = 0
    dut.rst_n.value = 0

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    dut.rst_n.value = 1

    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)


#Check that only the expected controller has permission
async def check_permission(dut, expected_controller):

    permissions = int(dut.permissions_out.value)

    if expected_controller is None:
        expected = 0
    else:
        expected = 1 << expected_controller

    assert permissions == expected, (
        f"Expected permissions_out = {expected:0{len(dut.permissions_out)}b}, "
        f"got {permissions:0{len(dut.permissions_out)}b}"
    )

    #There must never be more than one permission active
    assert permissions.bit_count() <= 1, (
        f"More than one permission active: "
        f"{permissions:0{len(dut.permissions_out)}b}"
    )


#Wait for one clock cycle and allow RTL signals to settle
async def clock_cycle(dut):
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)



#The tests:

"""
Tests reset the arbitter

Verifies:
- Reset behaviour
"""
@cocotb.test()
async def test_reset(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    await check_permission(dut, None)


"""
Tests a single permission

Verifies:
- Single permission request behaviour
- Permission is removed after request goes low
"""
@cocotb.test()
async def test_single_request(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    #Controller 1 requests the bus
    dut.requests_in.value = 0b010

    await clock_cycle(dut)

    await check_permission(dut, 1)

    #Controller 1 finishes
    dut.requests_in.value = 0b000

    await clock_cycle(dut)

    await check_permission(dut, None)


"""
Tests the FIFO queue

Verifies:
- Normal controllers are added to the end of the queue
- Controllers receive permission in the correct order
- Only one controller has permission at a time
"""
@cocotb.test()
async def test_queue_order(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    #Controller 2 requests first
    dut.requests_in.value = 0b100

    await clock_cycle(dut)

    await check_permission(dut, 2)

    #Controller 1 requests while controller 2 is using the bus
    dut.requests_in.value = 0b110

    await clock_cycle(dut)

    #Controller 2 must still have permission
    await check_permission(dut, 2)

    #Controller 2 finishes
    dut.requests_in.value = 0b010

    await clock_cycle(dut)

    #Controller 1 should now receive permission
    await check_permission(dut, 1)

    #Controller 1 finishes
    dut.requests_in.value = 0b000

    await clock_cycle(dut)

    await check_permission(dut, None)


"""
Tests the priority of controller 0

Verifies:
- Controller 0 is placed first in the queue
- Other controllers stay in the queue
- Queue continues normally after controller 0 finishes
"""
@cocotb.test()
async def test_controller_zero_priority(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    #Controller 2 requests first
    dut.requests_in.value = 0b100

    await clock_cycle(dut)

    await check_permission(dut, 2)

    #Controller 1 requests while controller 2 is active
    dut.requests_in.value = 0b110

    await clock_cycle(dut)

    await check_permission(dut, 2)

    #Controller 0 requests while controller 2 is active
    dut.requests_in.value = 0b111

    await clock_cycle(dut)

    #Controller 0 should have priority
    await check_permission(dut, 0)

    #Controller 0 finishes
    dut.requests_in.value = 0b110

    await clock_cycle(dut)

    #Controller 2 should continue
    await check_permission(dut, 2)

    #Controller 2 finishes
    dut.requests_in.value = 0b010

    await clock_cycle(dut)

    #Controller 1 should be next
    await check_permission(dut, 1)

    #Controller 1 finishes
    dut.requests_in.value = 0b000

    await clock_cycle(dut)

    await check_permission(dut, None)


"""
Tests that permission stays active

Verifies:
- Permission remains active while request stays high
- Permission is removed when request goes low
"""
@cocotb.test()
async def test_permission_stays_active(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    #Controller 1 requests the bus
    dut.requests_in.value = 0b010

    await clock_cycle(dut)

    #Keep the request active for several clock cycles
    for _ in range(5):

        await check_permission(dut, 1)

        await clock_cycle(dut)

    #Controller 1 finishes
    dut.requests_in.value = 0b000

    await clock_cycle(dut)

    await check_permission(dut, None)


"""
Tests simultaneous normal requests

Verifies:
- Multiple requests on the same clock cycle are stored
- Normal controllers are queued in index order
- No requests are lost
"""
@cocotb.test()
async def test_simultaneous_requests(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    #Controllers 1 and 2 request simultaneously
    dut.requests_in.value = 0b110

    await clock_cycle(dut)

    #Controller 1 should be first
    await check_permission(dut, 1)

    #Controller 1 finishes but controller 2 keeps requesting
    dut.requests_in.value = 0b100

    await clock_cycle(dut)

    #Controller 2 should now receive permission
    await check_permission(dut, 2)

    #Controller 2 finishes
    dut.requests_in.value = 0b000

    await clock_cycle(dut)

    await check_permission(dut, None)


"""
Tests simultaneous priority and normal requests

Verifies:
- Controller 0 receives priority
- Other simultaneous requests are not lost
- Normal controllers receive permission after controller 0 finishes
"""
@cocotb.test()
async def test_simultaneous_priority_request(dut):

    cocotb.start_soon(Clock(dut.clk, CLOCK_PERIOD, unit="ns").start())

    await reset_dut(dut)

    #Controllers 0 and 2 request simultaneously
    dut.requests_in.value = 0b101

    await clock_cycle(dut)

    #Controller 0 should receive permission
    await check_permission(dut, 0)

    #Controller 0 finishes but controller 2 keeps requesting
    dut.requests_in.value = 0b100

    await clock_cycle(dut)

    #Controller 2 should now receive permission
    await check_permission(dut, 2)

    #Controller 2 finishes
    dut.requests_in.value = 0b000

    await clock_cycle(dut)

    await check_permission(dut, None)