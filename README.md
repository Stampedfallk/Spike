# Spike
Measurement and control system for cacti and other house plants.

This file contains the following information about this project
- Overview
- How to use
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

## 2. How to use?
To use Spike exactly the way I used you will need an Arty Z7 10 FPGA-board, the sensors listed in the overview, and a pmod uart-usb transformer. In the constraints directory there is a constraint file which defines the physical connections. The ALS sensor is connected to the upper JA pmod port, the I2C sensors are connected to the upper JB pmod port and the usb-uart transformer to the lower JB pmod port.

To synthesize the design to the board you will need to use Vivado. In Vivado you need to change the standard of the VHDL-files to VHDL-2008 or newer. Once the design has been synthesized sw0 works as a reset, button 0 triggers the light measurement, button 1 triggers the hygro measurement, button 2 triggers the soil moisture measurement, and button 3 transfers the measured data through uart.

To read the measurements you need to run the read_data.py -program. For it to run you need to trigger all the measurements and then trigger the uart-transfer. Then the program will print the measured data.

Spike will work with other fpga-platforms as well. You just need to do your own constraints for them.

## 3. Status

### 11.11:
The project is fully operational. It can read light, temperature, humidity, and soil moisture data and send it to pc through uart.

## 4. System view
The top hierarchical level of this system is the fpga-top, which describes the top most blocks of the system. It contains the I2C_master module, sensor-interface module, and the uart module.

![Diagram](../Spike/Documentation/System_block_diagram.png)

The most interesting block in this is the sensor interface module. This module contains the controllers for all the sensors and other blocks that are required to make this system work.

![Diagram](../Spike/Documentation/Sensor_interface_block_diagram.png)

Further information about the IP blocks can found in their VHDL and testbench files.

## 5. Interfaces

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

## 6. Design Flow

### Project approach
The goal of the project was to design a complete FPGA-based environmental monitoring system capable of measuring ambient light, temperature, humidity, and soil moisture.

I approached this project by first finding suitable sensors that could be used together with Arty Z7 10 fpga-board which I already had. After finding the sensors I designed the architecture of the system.

### Development and simulation
Development followed an incremental approach, where each communication protocol and sensor interface was implemented and validated separately before integrating them into the complete system.

A reusable I²C subsystem was developed for the HYGRO and STEMMA sensors. The subsystem consists of a shared I²C master, an arbiter for bus access management, and dedicated sensor controllers. For the Pmod ALS, a separate SPI controller was implemented. Once individual interfaces were functional, the sensor subsystems were integrated into a common top-level design.

Verification was performed using cocotb and GHDL. Directed test cases were created for protocol transactions, controller state machines, sensor communication sequences, ACK/NACK handling, retry mechanisms, and data acquisition. Extensive waveform inspection was used to validate protocol timing and state transitions throughout development.

Hardware verification was performed on an Arty Z7-10 board using Vivado Integrated Logic Analyzer (ILA). The hardware testing phase focused on validating communication with physical sensors and resolving differences between simulation and real hardware behavior, particularly within I²C transactions and sensor response timing.

### System Implementation
The final system combines three independent sensing subsystems into a unified FPGA application.

The ALS subsystem acquires ambient light measurements using a custom SPI controller. Temperature and humidity measurements are obtained from the HDC1080 device on the Pmod HYGRO using a shared I²C infrastructure. Soil moisture measurements are collected from the Adafruit STEMMA Soil Sensor through the same I²C bus architecture.

Acquired sensor data is collected and packetized by a UART streaming module. The measurements are transmitted to a host computer through a UART interface, where a Python application receives, decodes, and converts raw sensor values into engineering units.
The completed design demonstrates a complete FPGA-based sensing pipeline, including sensor interfacing, protocol implementation, controller design, verification, hardware debugging, and external data communication.

## 7. Improvements

### 1. The implementation platform
FPGA-platform is probably a bit too powerfull for the needs of this project. Maybe this could also be implemented with a microcontroller unit.

### 2. Reading the data
Currently reading the measured data is a bit too complicated. If the system for example could share the data through my local WiFI network reading it would be easier.