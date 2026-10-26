-------------------------------------------------------------------------------
-- Title      : uart transmitter
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : uart_tx.vhd
-- Author     : Jere Nissinen
-- Edited     : 26.10.2026
-------------------------------------------------------------------------------
-- Description: UART transmitter module
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity uart_tx is 
    generic(
        ref_clk_freq_g : integer := 125000000;
        baud_rate_g : integer := 115200;
        byte_width_g : integer := 8
    );
    port(
        clk, rst_n : in std_logic;
        start_in : in std_logic;
        data_in : in std_logic_vector(byte_width_g-1 downto 0);
        tx_out : out std_logic;
        busy_out : out std_logic
    );
end uart_tx;

architecture rtl of uart_tx is 

    constant baud_divider_c : integer := ref_clk_freq_g/baud_rate_g;
    
    signal baud_counter_r : integer range 0 to baud_divider_c;
    signal data_r : std_logic_vector(byte_width_g-1 downto 0);
    signal bit_counter_r : integer range 0 to byte_width_g; --For tracking which bit we are sending

    type state_type is (idle, send_start, send_data, send_stop);
    signal curr_state_r : state_type;

begin
    --Calculating the bauds for sending the next data bit
    baud_counter : process(clk, rst_n)
    begin
        if(rst_n = '0') then
            baud_counter_r <= 0;

        elsif(clk'event and clk='1') then
            if(curr_state_r /= idle) then
                if(baud_counter_r = baud_divider_c) then
                    baud_counter_r <= 0;
                else
                    baud_counter_r <= baud_counter_r + 1;
                end if;

            else
                baud_counter_r <= 0;
            end if;
        end if;
    end process baud_counter;

    --General fsm logic
    fsm_process : process(clk, rst_n)
    begin
        if(rst_n = '0') then
            busy_out <= '0';
            tx_out <= '1';
            data_r <= (others => '0');
            curr_state_r <= idle;
            bit_counter_r <= 0;

        elsif(clk'event and clk='1') then
            case curr_state_r is
                when idle =>
                    busy_out <= '0';
                    tx_out <= '1';
                    bit_counter_r <= 0;

                    if(start_in = '1') then
                        busy_out <= '1';
                        data_r <= data_in;
                        curr_state_r <= send_start;
                    end if;
            
                when send_start =>
                    tx_out <= '0';
                    if(baud_counter_r = baud_divider_c) then
                        curr_state_r <= send_data;
                    end if;
                    
                when send_data =>
                    tx_out <= data_r(bit_counter_r);
                    if(baud_counter_r = baud_divider_c) then
                        if(bit_counter_r = byte_width_g - 1) then
                            curr_state_r <= send_stop;
                        else
                            bit_counter_r <= bit_counter_r + 1;
                        end if;
                    end if;
                
                when send_stop =>
                    tx_out <= '1';
                    if(baud_counter_r = baud_divider_c) then
                        curr_state_r <= idle;
                    end if;
            end case;
        end if;
    end process fsm_process;

end rtl;