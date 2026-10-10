-------------------------------------------------------------------------------
-- Title      : I2C master
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : i2c_master.vhd
-- Author     : Jere Nissinen
-- Edited     : 6.10.2026
-------------------------------------------------------------------------------
-- Description: Implements an i2c master logic which can be used to read and write throuhg
-- an i2c channel. A communication is triggered through the input pin start_in. Once this port
-- is high a communication begins. The i2c start condition happens and first the address is
-- sent. This address must be presented in the byte_in input. The last bit of the address determines
-- wheter we are in the read or write mode and the master reacts accordingly. Once a bite has either
-- been sent or received the master toggles the byte_done_out to tell the controller that the next byte can
-- be sent or received. If the master is in read mode the read bytes will show in the byte_out output.
-- If the last byte is being transmitted the controller must tell the master by toggling the 
-- end_in input. Then the master does to i2c end condition and goes back to idle.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity i2c_master is
    generic(
        ref_clk_freq_g : integer := 10000000;
        i2c_freq_g : integer := 20000;
        byte_width_g : integer := 8
    );
    port(
        clk, rst_n : in std_logic;
        start_in : in std_logic; --Triggers a i2c communication
        end_in : in std_logic; --Tells the master that this is the last byte
        byte_in : in std_logic_vector(byte_width_g-1 downto 0);
        sdat_inout : inout std_logic;
        sclk_out : out std_logic;
        byte_done_out : out std_logic; --Toggles high on the last bit of the byte
        byte_out : out std_logic_vector(byte_width_g-1 downto 0) --In read mode the byte out
    );
end i2c_master;

architecture rtl of i2c_master is

    constant sclk_divider_c : integer := ref_clk_freq_g/i2c_freq_g/2;
    constant sclk_half_c : integer := sclk_divider_c/2;

    signal sclk_r : std_logic;
    signal sclk_previous_r :std_logic;
    signal sdat_inout_r : std_logic;
    signal sdat_zen : std_logic;
    signal sdat_in : std_logic; --Normalized sda input.
    signal sclk_counter_r : integer range 0 to sclk_divider_c;
    signal bit_counter_r : integer range 0 to byte_width_g;

    type state_type is (idle, transmit_address, wait_ack, transmit_byte, receive_byte, send_ack, send_nack, end_state);
    signal curr_state_r : state_type;
    signal next_state : state_type; --This is used in wait_ack state to know where to move next
    signal previous_state : state_type; --This is used when we need to return to our last state (for example if we got nack)

begin

    sdat_in <= to_X01(sdat_inout);

    --Generates the sclk, while trnasmittion is on.
    sclk_handler : process(clk, rst_n)
    begin
        if(rst_n = '0') then
            sclk_r <= '1';
            sclk_previous_r <= '1';
            sclk_counter_r <= 0;

        elsif(clk'event and clk='1') then
            sclk_previous_r <= sclk_r;
            if(sclk_counter_r = sclk_divider_c) then
                sclk_r <= not sclk_r;
                sclk_counter_r <= 0;
            elsif(curr_state_r /= idle) then
                sclk_counter_r <= sclk_counter_r + 1;
            end if;
        end if;
    end process sclk_handler;

    sclk_out <= sclk_r;

    --The fsm logic:
    fsm_process : process(clk, rst_n)
    begin
        if(rst_n = '0') then
            sdat_inout_r <= '1';
            sdat_zen <= '0';
            bit_counter_r <= byte_width_g;
            curr_state_r <= idle;
            next_state <= idle;
            previous_state <= idle;
            byte_done_out <= '0';
            byte_out <= (others => '0');

        elsif(clk'event and clk='1') then
            case curr_state_r is

                when idle =>
                    --Transimttion started condition
                    if(start_in = '1') then
                        sdat_inout_r <= '0';
                        curr_state_r <= transmit_address;
                    end if;

                when transmit_address =>
                    --First transmit the i2c address and then determine the next actions from r/w bit
                    sdat_zen <= '0';
                    previous_state <= transmit_address;
                    if(sclk_r = '0' and sclk_counter_r = sclk_half_c) then --Transmit bit while sclk is low and not on edge
                        sdat_inout_r <= byte_in(bit_counter_r-1);
                        bit_counter_r <= bit_counter_r - 1;
                    end if;

                    if(sclk_r = '0' and sclk_previous_r = '1' and bit_counter_r = 0) then --Move to next state on lowering sclk and all bits are transmitted
                        if(sdat_inout_r = '0') then --Determine if we are reading or writing
                            next_state <= transmit_byte;
                        elsif(sdat_inout_r = '1') then
                            next_state <= receive_byte;
                        end if;

                        curr_state_r <= wait_ack;
                        sdat_zen <= '1';
                    end if;

                when wait_ack =>
                    if(sclk_r = '1' and sclk_counter_r = sclk_half_c) then --Read the ack on the rising edge
                        if(sdat_in = '0') then --got ack
                            byte_done_out <= '1';
                            curr_state_r <= next_state;
                        
                        elsif(sdat_in = '1') then --got nack
                            curr_state_r <= previous_state;
                        end if;
                    end if;
                    bit_counter_r <= byte_width_g;
                    

                when transmit_byte =>
                    byte_done_out <= '0';
                    sdat_zen <= '0';
                    previous_state <= transmit_byte;
                    if(sclk_r = '0' and sclk_counter_r = sclk_half_c) then --Transmit bit while sclk is low and not on edge
                        sdat_inout_r <= byte_in(bit_counter_r-1);
                        bit_counter_r <= bit_counter_r - 1;
                    end if;

                    if(sclk_r = '0' and sclk_previous_r = '1' and bit_counter_r = 0) then --Move to next state on lowering sclk and all bits are transmitted
                        if(end_in = '1') then --This was the last byte so moving on
                            next_state <= end_state;
                        else
                            next_state <= transmit_byte;
                        end if;

                        curr_state_r <= wait_ack;
                        sdat_zen <= '1';
                    end if;  
                    
                when receive_byte =>
                    byte_done_out <= '0';
                    previous_state <= receive_byte;
                    if(sclk_r = '0' and sclk_previous_r = '1' and bit_counter_r = 0) then --Determine the next actions
                        if(end_in = '1') then --If communication ends, then send nack 
                            sdat_zen <= '1';
                            sdat_inout_r <= '1';
                            curr_state_r <= send_nack;
                        else
                            sdat_zen <= '0'; --Put sdat down for ack
                            sdat_inout_r <= '0';
                            curr_state_r <= send_ack;
                        end if;
                        bit_counter_r <= byte_width_g;
                    end if;

                    if(sclk_r = '1' and sclk_previous_r = '0') then --Read sdat on rising edge and update output
                        byte_out(bit_counter_r - 1) <= sdat_in;
                        bit_counter_r <= bit_counter_r - 1;
                    end if;

                when send_ack => --Hold sdat down and release it after a cycle.
                    if(sclk_r = '0' and sclk_previous_r = '1') then
                        curr_state_r <= previous_state;
                        byte_done_out <= '1';
                        sdat_zen <= '1';
                    end if;

                when send_nack => --Send the final nack
                    if(sclk_r = '0' and sclk_previous_r = '1') then
                        curr_state_r <= end_state;
                        byte_done_out <= '1';
                        sdat_zen <= '1';
                        sdat_inout_r <= '1';
                    end if;
                
                when end_state => --Perform the end condition
                    byte_done_out <= '0';
                    sdat_zen <= '0';
                    sdat_inout_r <= '0';
                    if(sclk_r = '1' and sclk_counter_r = sclk_half_c) then
                        sdat_zen <= '1';
                        sdat_inout_r <= '1';
                        curr_state_r <= idle;
                    end if;
                end case;        

        end if;
    end process fsm_process;

    sdat_inout <= '0' 
        when (sdat_zen = '0' and sdat_inout_r = '0')
        else 'Z';

end rtl;