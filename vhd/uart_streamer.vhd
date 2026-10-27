-------------------------------------------------------------------------------
-- Title      : uart streamer
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : uart_streamer.vhd
-- Author     : Jere Nissinen
-- Edited     : 27.10.2026
-------------------------------------------------------------------------------
-- Description: UART streamer module for streaming sensor data
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity uart_streamer is
    generic(
        byte_width_g : integer := 8
    );
    port(
        clk, rst_n : in std_logic;
        trigger_transmittion_in : in std_logic;
        busy_in : in std_logic;
        light_in : in std_logic_vector(byte_width_g-1 downto 0);
        sensors_done_in : in std_logic; --Connect the sensor with the lowest priority here
        temperature_in : in std_logic_vector(2*byte_width_g-1 downto 0);
        humidity_in : in std_logic_vector(2*byte_width_g-1 downto 0);
        moisture_in : in std_logic_vector(2*byte_width_g-1 downto 0);
        start_out : out std_logic;
        byte_out : out std_logic_vector(byte_width_g-1 downto 0)
    );
end uart_streamer;

architecture rtl of uart_streamer is 
    type state_type is (idle, wait_for_sensors, light, temp_msb, temp_lsb, hum_msb, hum_lsb, moist_msb, moist_lsb);
    signal curr_state_r : state_type;
begin

    fsm_process : process(clk, rst_n)
    
    begin
        if(rst_n = '0') then
            byte_out <= (others => '0');
            start_out <= '0';
            curr_state_r <= idle;
        
        elsif(clk'event and clk = '1') then

            case curr_state_r is

            when idle =>
                byte_out <= (others => '0');
                start_out <= '0';
                if(trigger_transmittion_in = '1') then
                    curr_state_r <= wait_for_sensors;
                end if;

            when wait_for_sensors =>
                if(sensors_done_in = '0') then
                    curr_state_r <= light;
                end if;

            when light =>
                start_out <= '1';
                byte_out <= light_in;
                curr_state_r <= temp_msb;

            when temp_msb =>
                start_out <= '0';
                if(busy_in = '0') then
                    start_out <= '1';
                    byte_out <= temperature_in(2*byte_width_g-1 downto byte_width_g);
                    curr_state_r <= temp_lsb;
                end if;

            when temp_lsb =>
                start_out <= '0';
                if(busy_in = '0') then
                    start_out <= '1';
                    byte_out <= temperature_in(byte_width_g-1 downto 0);
                    curr_state_r <= hum_msb;
                end if;

            when hum_msb =>
                start_out <= '0';
                if(busy_in = '0') then
                    start_out <= '1';
                    byte_out <= humidity_in(2*byte_width_g-1 downto byte_width_g);
                    curr_state_r <= hum_lsb;
                end if;

            when hum_lsb =>
                start_out <= '0';
                if(busy_in = '0') then
                    start_out <= '1';
                    byte_out <= humidity_in(byte_width_g-1 downto 0);
                    curr_state_r <= moist_msb;
                end if;

            when moist_msb =>
                start_out <= '0';
                if(busy_in = '0') then
                    start_out <= '1';
                    byte_out <= moisture_in(2*byte_width_g-1 downto byte_width_g);
                    curr_state_r <= moist_lsb;
                end if;

            when moist_lsb =>
                start_out <= '0';
                if(busy_in = '0') then
                    start_out <= '1';
                    byte_out <= moisture_in(byte_width_g-1 downto 0);
                    curr_state_r <= idle;
                end if;
            end case;
        end if;
    end process fsm_process;
end rtl;