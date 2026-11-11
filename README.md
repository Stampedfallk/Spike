# Spike
Measurement and control system for cacti and other house plants.

This file contains the following information about this project
- Overview
- Status
- System view
- Interfaces
- Design flow
- Improvements

## 1. Overview
All in all this project might just be a excuse to buy more houseplants The idea of this system
is to gather data from the environment of a houseplant through different sensors. 

My implementation uses PMOD HYGRO HUMIDITY/TEMP SENSOR throuhg I2C interface, PMODALS AMBIENT 
LIGHT SENSOR through spi interface, and STEMMA SOIL SENSOR through the same I2C bus than the hygro sensor. With these sensors the system reads light level, air humidity, temperature, and soil moisture data.

The system then sends the data to pc through UART.

The RTL modules are mapped on ARTY Z7 10 FPGA board

My intention is to use this system mainly with cacti, but it is possible to use this with any other house plants as well.

## 2. Status

### 11.11:
The project is fully operational. It can read light, temperature, humidity, and soil moisture data and send it to pc through uart.

## 3. System view
The top hierarchical level of this system is the fpga-top, which describes the top most blocks of the system. It contains the I2C_master module, sensor-interface module, and the uart module.

![Diagram](../Spike/Documentation/System_block_diagram.png)

The most interesting block in this is the sensor interface module. This module contains the controllers for all the sensors and other blocks that are required to make this system work.

![Diagram](../Spike/Documentation/Sensor_interface_block_diagram.png)

Further information about the IP blocks can found in their VHDL and testbench files.

## 4. Interfaces

### System Clock

| Signal | Direction | Description |
|----------|-----------|-------------|
| `clk` | Input | 125 MHz system clock from the Arty Z7-10 board. |
| `rst_n` | Input | Active-low system reset. |

### User Inputs

| Signal | Direction | Description |
|----------|-----------|-------------|
| `buttons_in(0)` | Input | Trigger ambient light measurement (Pmod ALS). |
| `buttons_in(1)` | Input | Trigger temperature and humidity measurement (Pmod HYGRO). |
| `buttons_in(2)` | Input | Trigger soil moisture measurement (STEMMA Soil Sensor). |
| `buttons_in(3)` | Input | Trigger UART transmission of sensor data. |

### Pmod JA - Ambient Light Sensor

Digilent Pmod ALS connected through a custom SPI controller.

| Signal | Direction | Description |
|----------|-----------|-------------|
| `als_cs_out` | Output | SPI chip select. |
| `als_sclk_out` | Output | SPI serial clock. |
| `als_sdat_in` | Input | SPI serial data from sensor. |

Measured value:

- Ambient light intensity (8-bit)

### Pmod JB - Environmental Sensors

Shared I²C bus used by:

- Digilent Pmod HYGRO (HDC1080)
- Adafruit STEMMA Soil Sensor

| Signal | Direction | Description |
|----------|-----------|-------------|
| `i2c_sclk_out` | Output | I²C serial clock. |
| `i2c_sdat_inout` | Bidirectional | I²C serial data. |

Measured values:

- Temperature (16-bit)
- Relative humidity (16-bit)
- Soil moisture (16-bit)

### UART Interface

Sensor measurements are streamed to a host computer via UART.

| Signal | Direction | Description |
|----------|-----------|-------------|
| `tx_out` | Output | UART transmit line (115200 baud, 8-N-1). |

#### 

## 5. Design Flow

### Project approach
The goal of the project was to design a complete FPGA-based environmental monitoring system capable of measuring ambient light, temperature, humidity, and soil moisture.

I approached this project by first finding suitable sensors that could be used together with Arty Z7 10 fpga-board which I already had. After finding the sensors I designed the architecture of the system.

### Development and simulation

### Coding and simulation

## 6. Improvements