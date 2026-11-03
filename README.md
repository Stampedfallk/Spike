# Spike
Measurement and control system for cacti and other house plants.

This file contains the following information about this project
- Overview
- Status
- IP Blocks
- Interfaces
- Design flow
- Improvement

## 1. Overview
All in all this project might just be a excuse to buy more houseplants The idea of this system
is to gather data from the environment of a houseplant through different sensors. 

My implementation uses PMOD HYGRO HUMIDITY/TEMP SENSOR throuhg I2C interface, PMODALS AMBIENT 
LIGHT SENSOR through spi interface, and STEMMA SOIL SENSOR through the same I2C bus than the hygro sensor. With these sensors the system reads light level, air humidity, temperature, and soil moisture data.

The system then sends the data to pc through UART.

The RTL modules are mapped on ARTY Z7 10 FPGA board

My intention is to use this system mainly with cacti, but it is possible to use this with any other house plants as well.

## 2. Status

# 3.11:
Currently the sensor interface is fully operational. I can read data from all the sensors and inspect them through Vivado ILA.
UART should now be functional. I studied how I could get it working and I found out it would require a lot of work to use the uart through the processor on chip. I need an UART to USB bridge to validate my design and will look to obtain one shortly.

## 3. IP Blocks

## 4. Interfaces

## 5. Design Flow

### Project approach

### Coding and simulation

## 6. Improvement

... WORK IN PROGRESS ...