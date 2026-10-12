-------------------------------------------------------------------------------
-- Title      : I2C system tb wrapper
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : i2c_system_tb_wrapper.vhd
-- Author     : Jere Nissinen
-- Edited     : 12.10.2026
-------------------------------------------------------------------------------
-- Description: This file exists, because cocotb cannot drive sdat_inout. This file works
-- as a wrapper for testing the ic2 system.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity i2c_system_tb_wrapper is
end i2c_system_tb_wrapper;


architecture rtl of i2c_system_tb_wrapper is

    constant num_of_controllers_c : integer := 3;
    constant byte_width_c         : integer := 8;

    -- Cocotb controlled signals
    signal clk   : std_logic := '0';
    signal rst_n : std_logic := '0';

    -- Cocotb slave control:
    -- '1' = pull SDA low
    -- '0' = release SDA
    signal slave_sda_drive_low_in : std_logic := '0';

    -- I2C bus signals
    signal sdat_bus : std_logic;
    signal sdat_out : std_logic;
    signal sclk_out : std_logic;

    -- Arbiter signals
    signal requests    : std_logic_vector(num_of_controllers_c-1 downto 0);
    signal permissions : std_logic_vector(num_of_controllers_c-1 downto 0);

    -- Hygro config -> I2C master
    signal start          : std_logic;
    signal end_trans      : std_logic;
    signal byte_to_master : std_logic_vector(byte_width_c-1 downto 0);

    -- I2C master -> Hygro config
    signal byte_done : std_logic;

    signal byte_from_master : std_logic_vector(byte_width_c-1 downto 0);

begin

    -- I2C ARBITER
    i2c_arbitter_inst : entity work.i2c_arbitter
        generic map(
            num_of_controllers_g => num_of_controllers_c
        )
        port map(
            clk             => clk,
            rst_n           => rst_n,
            requests_in     => requests,
            permissions_out => permissions
        );

    -- HYGRO CONFIG
    -- Controller index 0
    hygro_config_inst : entity work.hygro_config
        generic map(
            byte_width_g => byte_width_c
        )
        port map(
            clk                    => clk,
            rst_n                  => rst_n,
            permission_in          => permissions(0),
            byte_done_in           => byte_done,
            request_permission_out => requests(0),
            start_out              => start,
            end_out                => end_trans,
            byte_out               => byte_to_master
        );

    -- UNUSED ARBITER REQUESTS
    requests(1) <= '0';
    requests(2) <= '0';

    -- I2C MASTER
    i2c_master_inst : entity work.i2c_master
        generic map(
            ref_clk_freq_g => 10000000,
            i2c_freq_g     => 20000,
            byte_width_g   => byte_width_c
        )
        port map(
            clk           => clk,
            rst_n         => rst_n,
            start_in      => start,
            end_in        => end_trans,
            byte_in       => byte_to_master,

            sdat_inout    => sdat_bus,
            sclk_out      => sclk_out,

            byte_done_out => byte_done,
            byte_out      => byte_from_master
        );

    -- I2C SDA PULL-UP
    sdat_bus <= 'H';

    -- COCOTB SLAVE SDA DRIVER
    --
    -- Open-drain:
    --   1 -> drive SDA low
    --   0 -> release SDA
    sdat_bus <= '0'
        when slave_sda_drive_low_in = '1'
        else 'Z';

    -- COCOTB SDA OBSERVATION
    sdat_out <= sdat_bus;

end rtl;