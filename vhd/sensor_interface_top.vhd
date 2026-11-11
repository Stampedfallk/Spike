-------------------------------------------------------------------------------
-- Title      : Sensor interfacec top
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : sensor_interface_top.vhd
-- Author     : Jere Nissinen
-- Edited     : 20.10.2026
-------------------------------------------------------------------------------
-- Description: Top module for communicating with all the sensors and i2c_master
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity sensor_interface_top is
    generic(
        byte_width_g    : integer := 8;
        sclk_freq_g     : integer := 1000000;
        ref_clk_freq_g  : integer := 125000000;
        num_buttons_g   : integer := 3
    );

    port(
        clk                     : in std_logic;
        rst_n                   : in std_logic;
        buttons_in              : in std_logic_vector(num_buttons_g-1 downto 0);
        ack_in                  : in std_logic;
        sdat_in                 : in std_logic;
        byte_done_in            : in std_logic;
        byte_from_i2c_master_in : in std_logic_vector(byte_width_g-1 downto 0);

        cs_out          : out std_logic;
        sclk_out        : out std_logic;
        start_out       : out std_logic;
        end_out         : out std_logic;
        byte_out        : out std_logic_vector(byte_width_g-1 downto 0);

        light_out       : out std_logic_vector(byte_width_g-1 downto 0);
        moisture_out    : out std_logic_vector(2*byte_width_g-1 downto 0);
        humidity_out    : out std_logic_vector(2*byte_width_g-1 downto 0);
        temperature_out : out std_logic_vector(2*byte_width_g-1 downto 0)
    );
end sensor_interface_top;


architecture structural of sensor_interface_top is

    --Control signals for I2C controllers
    signal hygro_config_start : std_logic;
    signal hygro_config_end   : std_logic;
    signal hygro_config_byte  : std_logic_vector(byte_width_g-1 downto 0);

    signal hygro_read_start : std_logic;
    signal hygro_read_end   : std_logic;
    signal hygro_read_byte  : std_logic_vector(byte_width_g-1 downto 0);

    signal stemma_read_start : std_logic;
    signal stemma_read_end   : std_logic;
    signal stemma_read_byte  : std_logic_vector(byte_width_g-1 downto 0);

    --Arbiter signals
    signal requests    : std_logic_vector(num_buttons_g-1 downto 0);
    signal permissions : std_logic_vector(num_buttons_g-1 downto 0);

    --Top -> I2C master
    signal start          : std_logic;
    signal end_trans      : std_logic;
    signal byte_to_master : std_logic_vector(byte_width_g-1 downto 0);


    component light_sensor_ctrl is
        generic(
            data_width_g   : integer := 8;
            sclk_freq_g    : integer := 1000000;
            ref_clk_freq_g : integer := 10000000
        );

        port(
            clk                    : in std_logic;
            rst_n                  : in std_logic;
            sdata_in               : in std_logic;
            trigger_measurement_in : in std_logic;
            cs_out                 : out std_logic;
            sclk_out               : out std_logic;
            data_out               : out std_logic_vector(data_width_g-1 downto 0)
        );
    end component;


    component i2c_arbitter is
        generic(
            num_of_controllers_g : integer := 3
        );

        port(
            clk             : in std_logic;
            rst_n           : in std_logic;
            requests_in     : in std_logic_vector(num_of_controllers_g-1 downto 0);
            permissions_out : out std_logic_vector(num_of_controllers_g-1 downto 0)
        );
    end component;


    component hygro_config is
        generic(
            byte_width_g : integer := 8
        );

        port(
            clk                    : in std_logic;
            rst_n                  : in std_logic;
            permission_in          : in std_logic;
            ack_in                 : in std_logic;
            byte_done_in           : in std_logic;
            request_permission_out : out std_logic;
            start_out              : out std_logic;
            end_out                : out std_logic;
            byte_out               : out std_logic_vector(byte_width_g-1 downto 0)
        );
    end component;


    component hygro_read_ctrl is
        generic(
            byte_width_g : integer := 8
        );

        port(
            clk                    : in std_logic;
            rst_n                  : in std_logic;
            permission_in          : in std_logic;
            byte_done_in           : in std_logic;
            ack_in                 : in std_logic;
            byte_in                : in std_logic_vector(byte_width_g-1 downto 0);
            trigger_measurement_in : in std_logic;
            request_permission_out : out std_logic;
            start_out              : out std_logic;
            end_out                : out std_logic;
            byte_out               : out std_logic_vector(byte_width_g-1 downto 0);
            temperature_out        : out std_logic_vector(2*byte_width_g-1 downto 0);
            humidity_out           : out std_logic_vector(2*byte_width_g-1 downto 0)
        );
    end component;


    component stemma_read_ctrl is
        generic(
            byte_width_g : integer := 8
        );

        port(
            clk                    : in std_logic;
            rst_n                  : in std_logic;
            permission_in          : in std_logic;
            ack_in                 : in std_logic;
            byte_done_in           : in std_logic;
            byte_in                : in std_logic_vector(byte_width_g-1 downto 0);
            trigger_measurement_in : in std_logic;
            request_permission_out : out std_logic;
            start_out              : out std_logic;
            end_out                : out std_logic;
            byte_out               : out std_logic_vector(byte_width_g-1 downto 0);
            soil_moisture_out      : out std_logic_vector(2*byte_width_g-1 downto 0)
        );
    end component;

begin

    light_sensor_ctrl_inst : light_sensor_ctrl
        generic map(
            data_width_g   => byte_width_g,
            sclk_freq_g    => sclk_freq_g,
            ref_clk_freq_g => ref_clk_freq_g
        )
        port map(
            clk                    => clk,
            rst_n                  => rst_n,
            sdata_in               => sdat_in,
            trigger_measurement_in => buttons_in(0),
            cs_out                 => cs_out,
            sclk_out               => sclk_out,
            data_out               => light_out
        );


    i2c_arbitter_inst : i2c_arbitter
        generic map(
            num_of_controllers_g => num_buttons_g
        )
        port map(
            clk             => clk,
            rst_n           => rst_n,
            requests_in     => requests,
            permissions_out => permissions
        );


    hygro_config_inst : hygro_config
        generic map(
            byte_width_g => byte_width_g
        )
        port map(
            clk                    => clk,
            rst_n                  => rst_n,
            permission_in          => permissions(0),
            ack_in                 => ack_in,
            byte_done_in           => byte_done_in,
            request_permission_out => requests(0),
            start_out              => hygro_config_start,
            end_out                => hygro_config_end,
            byte_out               => hygro_config_byte
        );


    hygro_read_ctrl_inst : hygro_read_ctrl
        generic map(
            byte_width_g => byte_width_g
        )
        port map(
            clk                    => clk,
            rst_n                  => rst_n,
            permission_in          => permissions(1),
            byte_done_in           => byte_done_in,
            byte_in                => byte_from_i2c_master_in,
            ack_in                 => ack_in,
            trigger_measurement_in => buttons_in(1),
            request_permission_out => requests(1),
            start_out              => hygro_read_start,
            end_out                => hygro_read_end,
            byte_out               => hygro_read_byte,
            temperature_out        => temperature_out,
            humidity_out           => humidity_out
        );


    stemma_read_ctrl_inst : stemma_read_ctrl
        generic map(
            byte_width_g => byte_width_g
        )
        port map(
            clk                    => clk,
            rst_n                  => rst_n,
            permission_in          => permissions(2),
            byte_done_in           => byte_done_in,
            byte_in                => byte_from_i2c_master_in,
            ack_in                 => ack_in,
            trigger_measurement_in => buttons_in(2),
            request_permission_out => requests(2),
            start_out              => stemma_read_start,
            end_out                => stemma_read_end,
            byte_out               => stemma_read_byte,
            soil_moisture_out      => moisture_out
        );


    process(all)
    begin
        start          <= '0';
        end_trans      <= '0';
        byte_to_master <= (others => '0');

        if(permissions(0) = '1') then
            start          <= hygro_config_start;
            end_trans      <= hygro_config_end;
            byte_to_master <= hygro_config_byte;

        elsif(permissions(1) = '1') then
            start          <= hygro_read_start;
            end_trans      <= hygro_read_end;
            byte_to_master <= hygro_read_byte;

        elsif(permissions(2) = '1') then
            start          <= stemma_read_start;
            end_trans      <= stemma_read_end;
            byte_to_master <= stemma_read_byte;
        end if;
    end process;


    start_out <= start;
    end_out   <= end_trans;
    byte_out  <= byte_to_master;

end structural;