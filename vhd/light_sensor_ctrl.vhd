-------------------------------------------------------------------------------
-- Title      : Light sensor controller
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : light_sensor_ctrl.vhd
-- Author     : Jere Nissinen
-- Edited     : 2.10.2026
-------------------------------------------------------------------------------
-- Description: Implements controller interface for PMODALS AMBIENT LIGHT SENSOR. the sensor
-- uses ADC081S021 8-bit A/D converter for communication. The sensor is controlled with cs and sclk signals,
-- and it uses the sdata signal to send data to our controller. The start condition for the data transaction
-- is lowering of the cs-signal. Once the cs is lowered the sclk generation begins. This transaction consists
-- of 15 bits. At the beginning there ate 3 0-bits, then 8 data bits followed by 4 0-bits. sdata is read on
-- the rising edge of the sclk. The transaction is triggered by the trigger_measurement signal and the
-- gained data can be read through the data_out port.
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity light_sensor_ctrl is

    generic(
        data_width_g    : integer := 8;
        sclk_freq_g     : integer := 1000000; --sclk frequency 1MHZ
        ref_clk_freq_g  : integer := 10000000 --reference for creating the sclk. MUST BE ADJUSTED TO THE FREQUENCY YOU ARE USIGN!
    );

    port(
        clk, rst_n              : in std_logic;
        sdata_in                : in std_logic;
        trigger_measurement_in  : in std_logic;
        cs_out                  : out std_logic;
        sclk_out                : out std_logic;
        data_out                : out std_logic_vector(data_width_g-1 downto 0)
    );

end light_sensor_ctrl;

architecture rtl of light_sensor_ctrl is

    constant sclk_divider_c             : integer := ref_clk_freq_g/sclk_freq_g/2;
    constant amount_of_start_zeros_c    : integer := 3;
    constant amount_of_data_bits_c      : integer := 8;
    constant amount_of_end_zeros_c      : integer := 4;

    signal cs_r             : std_logic;
    signal sclk_r           : std_logic;
    signal previous_sclk_r  : std_logic; --This signal is used for detecting the rising edge of the sclk.
    signal sclk_counter     : integer range 0 to sclk_divider_c;
    signal current_bit      : integer range 0 to data_width_g;
    
    --Fsm for different parts of the transaction
    type state_type is (idle, receive_start_zeros, receive_measurement, receive_end_zeros);
    signal curr_state_r: state_type;

begin

    --Generation of slck, while cs is low.
    sclk_generator : process(clk, rst_n)
    begin
        if(rst_n ='0') then
            sclk_r <= '1';
            previous_sclk_r <= '1';
            sclk_counter <= 0;

        elsif (clk'event and clk = '1') then
            if(cs_r = '0') then
                if(sclk_counter = sclk_divider_c) then
                    previous_sclk_r <= sclk_r;
                    sclk_r <= not sclk_r;
                    sclk_counter <= 0;
                else
                    previous_sclk_r <= sclk_r;
                    sclk_counter <= sclk_counter + 1;
                end if;
            else
                sclk_r <= '1';
            end if;
        end if;
    end process sclk_generator;

    sclk_out <= sclk_r;
    cs_out <= cs_r;

    --Waiting for start of transaction and then going through with the transaction.
    fsm_process : process(clk, rst_n)
    begin
        if(rst_n='0') then
            cs_r <= '1';
            curr_state_r <= idle;
            data_out <= (others => '0');
            current_bit <= 0;

        elsif(clk'event and clk = '1') then

            case curr_state_r is

                when idle =>
                    --Measurement starts.
                    if(trigger_measurement_in = '1') then
                        cs_r <= '0';
                        curr_state_r <= receive_start_zeros; 
                    else
                        cs_r <= '1';
                    end if;

                when receive_start_zeros =>
                    --Wait for the rising edge of the sclk and then read inputs. Once
                    --the correct amount inputs have been handled go to next state.
                    --works similarly in every state. In case of an error it goes back to idle.
                    if(sclk_r = '1' and sclk_r /= previous_sclk_r) then
                        if(sdata_in = '0') then
                            if(current_bit = amount_of_start_zeros_c - 1) then
                                curr_state_r <= receive_measurement;
                                current_bit <= 0;
                            else
                                current_bit <= current_bit + 1;
                            end if;
                        else
                            curr_state_r <= idle;
                        end if;
                    end if;

                when receive_measurement =>
                    if(sclk_r = '1' and sclk_r /= previous_sclk_r) then
                        if(current_bit = amount_of_data_bits_c - 1) then
                            curr_state_r <= receive_end_zeros;
                            data_out(data_width_g - current_bit - 1) <= sdata_in;
                            current_bit <= 0;
                        else
                            data_out(data_width_g - current_bit - 1) <= sdata_in;
                            current_bit <= current_bit + 1;
                        end if;
                    end if;

                when receive_end_zeros =>
                    if(sclk_r = '1' and sclk_r /= previous_sclk_r) then
                        if(sdata_in = '0') then
                            if(current_bit = amount_of_end_zeros_c - 1) then
                                curr_state_r <= idle;
                                current_bit <= 0;
                            else
                                current_bit <= current_bit + 1;
                            end if;
                        else
                            curr_state_r <= idle;
                        end if;                        
                    end if;
                end case;

        end if;
    end process fsm_process;

end rtl;