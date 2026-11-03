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
        temperature_in : in std_logic_vector(2*byte_width_g-1 downto 0);
        humidity_in : in std_logic_vector(2*byte_width_g-1 downto 0);
        moisture_in : in std_logic_vector(2*byte_width_g-1 downto 0);
        start_out : out std_logic;
        byte_out : out std_logic_vector(byte_width_g-1 downto 0)
    );
end uart_streamer;

architecture rtl of uart_streamer is
    type state_type is (idle, send_byte, wait_busy_high, wait_busy_low);
    signal curr_state_r : state_type;
    signal byte_idx_r   : integer range 0 to 6;
begin

    fsm_process : process(clk, rst_n)
    begin
        if(rst_n = '0') then
            byte_out     <= (others => '0');
            start_out    <= '0';
            byte_idx_r   <= 0;
            curr_state_r <= idle;

        elsif(clk'event and clk = '1') then
            start_out <= '0';

            case curr_state_r is

            when idle =>
                byte_idx_r <= 0;
                if(trigger_transmittion_in = '1') then
                    curr_state_r <= send_byte;
                end if;

            when send_byte =>
                if(busy_in = '0') then
                    start_out <= '1';
                    case byte_idx_r is
                        when 0 => byte_out <= light_in;
                        when 1 => byte_out <= temperature_in(2*byte_width_g-1 downto byte_width_g);
                        when 2 => byte_out <= temperature_in(byte_width_g-1 downto 0);
                        when 3 => byte_out <= humidity_in(2*byte_width_g-1 downto byte_width_g);
                        when 4 => byte_out <= humidity_in(byte_width_g-1 downto 0);
                        when 5 => byte_out <= moisture_in(2*byte_width_g-1 downto byte_width_g);
                        when 6 => byte_out <= moisture_in(byte_width_g-1 downto 0);
                    end case;
                    curr_state_r <= wait_busy_high;
                end if;

            --Wait that uart_tx has taken the byte
            when wait_busy_high =>
                if(busy_in = '1') then
                    curr_state_r <= wait_busy_low;
                end if;

            --Wait for sent byte
            when wait_busy_low =>
                if(busy_in = '0') then
                    if(byte_idx_r = 6) then
                        curr_state_r <= idle;
                    else
                        byte_idx_r   <= byte_idx_r + 1;
                        curr_state_r <= send_byte;
                    end if;
                end if;
            end case;
        end if;
    end process fsm_process;
end rtl;