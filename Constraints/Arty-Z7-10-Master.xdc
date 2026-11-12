## ============================================================
## Clock - 125 MHz
## ============================================================

set_property -dict {PACKAGE_PIN H16 IOSTANDARD LVCMOS33} [get_ports clk]
create_clock -period 8.000 -name sys_clk_pin -waveform {0.000 4.000} -add [get_ports clk]


## ============================================================
## Reset - SW0
## ============================================================

set_property -dict {PACKAGE_PIN M20 IOSTANDARD LVCMOS33} [get_ports rst_n]


## ============================================================
## Buttons
## BTN0 - ALS
## BTN1 - HYGRO
## BTN2 - STEMMA soil moisture
## ============================================================

set_property -dict {PACKAGE_PIN D19 IOSTANDARD LVCMOS33} [get_ports {buttons_in[0]}]
set_property -dict {PACKAGE_PIN D20 IOSTANDARD LVCMOS33} [get_ports {buttons_in[1]}]
set_property -dict {PACKAGE_PIN L20 IOSTANDARD LVCMOS33} [get_ports {buttons_in[2]}]
set_property -dict {PACKAGE_PIN L19 IOSTANDARD LVCMOS33} [get_ports {buttons_in[3]}]

## ============================================================
## Pmod JA - ALS
## ============================================================

set_property -dict {PACKAGE_PIN Y18 IOSTANDARD LVCMOS33} [get_ports als_cs_out]
set_property -dict {PACKAGE_PIN Y16 IOSTANDARD LVCMOS33} [get_ports als_sdat_in]
set_property -dict {PACKAGE_PIN Y17 IOSTANDARD LVCMOS33} [get_ports als_sclk_out]


## ============================================================
## Pmod JB - I2C
## ============================================================
set_property -dict {PACKAGE_PIN T11 IOSTANDARD LVCMOS33} [get_ports i2c_sclk_out]
set_property -dict {PACKAGE_PIN T10 IOSTANDARD LVCMOS33} [get_ports i2c_sdat_inout]


## ============================================================
## Pmod JB (lower) - USBUART
## Pin 8 (RXD) <- FPGA TX
## ============================================================

set_property -dict {PACKAGE_PIN W16 IOSTANDARD LVCMOS33} [get_ports tx_out]