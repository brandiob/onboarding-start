# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

# --- configuration Constants ---
PWM_PERIOD_CYCLES = 4000
PWM_MIN_FREQ_HZ = 2970
PWM_MAX_FREQ_HZ = 3030

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    """
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data

    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")

    first_byte = (int(r_w) << 7) | address
    sclk = 0
    ncs = 0
    bit = 0

    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)

    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)

    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)

    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

# ////////////////////////
# Brandon's portion below
# ////////////////////////

# --- helpers ---

def sample_target_pwm_bit(dut):
    """returns the status of the target pin"""
    return int(dut.uo_out.value) & 1

async def reset_dut(dut):
    """clock"""
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0) # CS high, idle
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

async def setup_pwm_output(dut, duty_value):
    """config"""
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 0x01)
    await send_spi_transaction(dut, 1, 0x04, duty_value)
    await ClockCycles(dut.clk, 100)

async def measure_pwm_period_ns(dut):
    previous_state = sample_target_pwm_bit(dut)
    first_edge = None
    for _ in range(50000):
        await RisingEdge(dut.clk)
        current_state = sample_target_pwm_bit(dut)
        if previous_state == 0 and current_state == 1:
            first_edge = cocotb.utils.get_sim_time(unit="ns")
            break
        previous_state = current_state

    for _ in range(50000):
        await RisingEdge(dut.clk)
        current_state = sample_target_pwm_bit(dut)
        if previous_state == 0 and current_state == 1:
            second_edge = cocotb.utils.get_sim_time(unit="ns")
            return second_edge - first_edge
        previous_state = current_state
    raise TimeoutError("Failed to catch PWM period edges")

async def measure_pwm_duty_percent(dut):

    previous_state = sample_target_pwm_bit(dut)
    t_rise, t_fall, t_next_rise = None, None, None
    
    for _ in range(50000):
        await RisingEdge(dut.clk)
        current_state = sample_target_pwm_bit(dut)
        if previous_state == 0 and current_state == 1:
            t_rise = cocotb.utils.get_sim_time(unit="ns")
            break
        previous_state = current_state

    for _ in range(50000):
        await RisingEdge(dut.clk)
        current_state = sample_target_pwm_bit(dut)
        if previous_state == 1 and current_state == 0:
            t_fall = cocotb.utils.get_sim_time(unit="ns")
            break
        previous_state = current_state

    for _ in range(50000):
        await RisingEdge(dut.clk)
        current_state = sample_target_pwm_bit(dut)
        if previous_state == 0 and current_state == 1:
            t_next_rise = cocotb.utils.get_sim_time(unit="ns")
            break
        previous_state = current_state

    return ((t_fall - t_rise) / (t_next_rise - t_rise)) * 100.0

# --- My Test Cases ---

@cocotb.test()
async def test_pwm_freq(dut):
    dut._log.info("Starting Functional PWM Frequency Validation...")
    # Start the clock for this test block
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    await setup_pwm_output(dut, 0x80)

    period_ns = await measure_pwm_period_ns(dut)
    frequency_hz = 1_000_000_000 / period_ns

    assert PWM_MIN_FREQ_HZ <= frequency_hz <= PWM_MAX_FREQ_HZ, (
        f"Expected PWM frequency between {PWM_MIN_FREQ_HZ} Hz and "
        f"{PWM_MAX_FREQ_HZ} Hz, got {frequency_hz:.2f} Hz"
    )
    dut._log.info(f"PWM frequency: {frequency_hz:.2f} Hz")


@cocotb.test()
async def test_pwm_duty(dut):
    dut._log.info("Starting Functional PWM Duty Cycle Boundary Validation...")
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)

    # A: Master Output Enable Override Check
    await send_spi_transaction(dut, 1, 0x00, 0x00)
    await send_spi_transaction(dut, 1, 0x02, 0x01)
    await send_spi_transaction(dut, 1, 0x04, 0x80)
    for _ in range(PWM_PERIOD_CYCLES):
        await RisingEdge(dut.clk)
        assert sample_target_pwm_bit(dut) == 0, "Expected output value bit 0 low to override PWM"

    # B: 0% Duty Cycle Boundary Check
    await setup_pwm_output(dut, 0x00)
    for _ in range(PWM_PERIOD_CYCLES):
        await RisingEdge(dut.clk)
        assert sample_target_pwm_bit(dut) == 0, "Expected 0% duty cycle to stay low"

    # C: 50% Active Modulation Duty Measurement
    await setup_pwm_output(dut, 0x80)
    duty_percent = await measure_pwm_duty_percent(dut)
    assert 49 <= duty_percent <= 51, f"Expected 50% duty cycle, got {duty_percent:.2f}%"

    # D: 100% Duty Cycle Boundary Check
    await setup_pwm_output(dut, 0xFF)
    for _ in range(PWM_PERIOD_CYCLES):
        await RisingEdge(dut.clk)
        assert sample_target_pwm_bit(dut) == 1, "Expected 100% duty cycle to stay high"

    dut._log.info(f"PWM duty cycle at 0x80: {duty_percent:.2f}%")
    dut._log.info("PWM Duty Cycle test completed successfully")