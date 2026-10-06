-------------------------------------------------------------------------------
-- Title      : I2C master tb wrapper
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : i2c_master_tb_wrapper.vhd
-- Author     : Jere Nissinen
-- Edited     : 5.10.2026
-------------------------------------------------------------------------------
-- Description: This file exists, because cocotb cannot drive sdat_inout. This file works
-- as a wrapper for testing the ic2_master. Through this file we can drive values to sdat for
-- i2c_master to read them.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity i2c_master_tb_wrapper is
    
    generic(
        ref_clk_freq_g : integer := 10000000;
        i2c_freq_g : integer := 20000;
        byte_width_g : integer := 8
    );

    port(
        clk, rst_n : in std_logic; --almost same porst as in the master
        start_in : in std_logic;
        end_in : in std_logic;
        byte_in : in std_logic_vector(byte_width_g-1 downto 0);
        sclk_out : out std_logic;
        byte_done_out : out std_logic;
        byte_out : out std_logic_vector(byte_width_g-1 downto 0);

        slave_sda_drive_low_in : in std_logic; --cocotb controls this signal to drive in values to the dut

        sdat_out : out std_logic
    );
end entity i2c_master_tb_wrapper;

architecture rtl of i2c_master_tb_wrapper is

    signal sdat_bus : std_logic;

begin
    --instantiating the dut
    dut_i : entity work.i2c_master

        generic map (
            ref_clk_freq_g => ref_clk_freq_g,
            i2c_freq_g => i2c_freq_g,
            byte_width_g => byte_width_g
        )

        port map (
            clk => clk,
            rst_n => rst_n,
            start_in => start_in,
            end_in => end_in,
            byte_in => byte_in,
            sdat_inout => sdat_bus,
            sclk_out => sclk_out,
            byte_done_out => byte_done_out,
            byte_out => byte_out
        );

    sdat_bus <= '0' when slave_sda_drive_low_in = '1' else 'Z';

    sdat_bus <= 'H';

    sdat_out <= sdat_bus;

end rtl;