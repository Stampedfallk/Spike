-------------------------------------------------------------------------------
-- Title      : fpga top
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : fpga_top.vhd
-- Author     : Jere Nissinen
-- Edited     : 20.10.2026
-------------------------------------------------------------------------------
-- Description: Top module for the fpga implementation. Connects with physical io ports of the development board.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity fpga_top is
    generic(
        byte_width_g   : integer := 8;
        sclk_freq_g    : integer := 1000000;
        ref_clk_freq_g : integer := 125000000;
        i2c_freq_g     : integer := 100000;
        num_buttons_g  : integer := 3
    );

    port(
        clk        : in std_logic;
        rst_n      : in std_logic;
        buttons_in : in std_logic_vector(num_buttons_g-1 downto 0);

        -- Pmod JA - ALS
        als_sdat_in  : in  std_logic;
        als_cs_out   : out std_logic;
        als_sclk_out : out std_logic;

        -- Pmod JB - I2C
        i2c_sdat_inout : inout std_logic;
        i2c_sclk_out   : out std_logic
    );
end fpga_top;


architecture structural of fpga_top is

    -- Sensor interface -> I2C master
    signal start          : std_logic;
    signal end_trans      : std_logic;
    signal byte_to_master : std_logic_vector(byte_width_g-1 downto 0);

    -- I2C master -> sensor interface
    signal byte_done        : std_logic;
    signal byte_from_master : std_logic_vector(byte_width_g-1 downto 0);
    signal ack              : std_logic;

    -- Sensor values
    signal light       : std_logic_vector(byte_width_g-1 downto 0);
    signal moisture    : std_logic_vector(2*byte_width_g-1 downto 0);
    signal humidity    : std_logic_vector(2*byte_width_g-1 downto 0);
    signal temperature : std_logic_vector(2*byte_width_g-1 downto 0);

    --Make the signals readable for early fpga debug
    attribute mark_debug : string;

    attribute mark_debug of light : signal is "true";
    attribute mark_debug of moisture : signal is "true";
    attribute mark_debug of humidity : signal is "true";
    attribute mark_debug of temperature : signal is "true";


    component sensor_interface_top is
        generic(
            byte_width_g   : integer := 8;
            sclk_freq_g    : integer := 1000000;
            ref_clk_freq_g : integer := 125000000;
            num_buttons_g  : integer := 3
        );

        port(
            clk                     : in std_logic;
            rst_n                   : in std_logic;
            buttons_in              : in std_logic_vector(num_buttons_g-1 downto 0);
            sdat_in                 : in std_logic;
            byte_done_in            : in std_logic;
            byte_from_i2c_master_in : in std_logic_vector(byte_width_g-1 downto 0);
            ack_in                  : in std_logic;

            cs_out    : out std_logic;
            sclk_out  : out std_logic;
            start_out : out std_logic;
            end_out   : out std_logic;
            byte_out  : out std_logic_vector(byte_width_g-1 downto 0);

            light_out       : out std_logic_vector(byte_width_g-1 downto 0);
            moisture_out    : out std_logic_vector(2*byte_width_g-1 downto 0);
            humidity_out    : out std_logic_vector(2*byte_width_g-1 downto 0);
            temperature_out : out std_logic_vector(2*byte_width_g-1 downto 0)
        );
    end component;


    component i2c_master is
        generic(
            ref_clk_freq_g : integer := 10000000;
            i2c_freq_g     : integer := 20000;
            byte_width_g   : integer := 8
        );

        port(
            clk           : in std_logic;
            rst_n         : in std_logic;
            start_in      : in std_logic;
            end_in        : in std_logic;
            byte_in       : in std_logic_vector(byte_width_g-1 downto 0);
            sdat_inout    : inout std_logic;
            sclk_out      : out std_logic;
            byte_done_out : out std_logic;
            ack_out       : out std_logic;
            byte_out      : out std_logic_vector(byte_width_g-1 downto 0)
        );
    end component;

begin

    sensor_interface_inst : sensor_interface_top
        generic map(
            byte_width_g   => byte_width_g,
            sclk_freq_g    => sclk_freq_g,
            ref_clk_freq_g => ref_clk_freq_g,
            num_buttons_g  => num_buttons_g
        )
        port map(
            clk                     => clk,
            rst_n                   => rst_n,
            buttons_in              => buttons_in,

            -- ALS
            sdat_in                 => als_sdat_in,
            cs_out                  => als_cs_out,
            sclk_out                => als_sclk_out,

            -- I2C master interface
            byte_done_in            => byte_done,
            ack_in                  => ack,
            byte_from_i2c_master_in => byte_from_master,
            start_out               => start,
            end_out                 => end_trans,
            byte_out                => byte_to_master,

            -- Sensor results
            light_out               => light,
            moisture_out            => moisture,
            humidity_out            => humidity,
            temperature_out         => temperature
        );


    i2c_master_inst : i2c_master
        generic map(
            ref_clk_freq_g => ref_clk_freq_g,
            i2c_freq_g     => i2c_freq_g,
            byte_width_g   => byte_width_g
        )
        port map(
            clk           => clk,
            rst_n         => rst_n,

            -- Sensor interface
            start_in      => start,
            end_in        => end_trans,
            byte_in       => byte_to_master,
            byte_done_out => byte_done,
            byte_out      => byte_from_master,
            ack_out       => ack,

            -- Physical I2C bus
            sdat_inout    => i2c_sdat_inout,
            sclk_out      => i2c_sclk_out
        );

end structural;