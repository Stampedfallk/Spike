-------------------------------------------------------------------------------
-- Title      : HYGRO HUMIDITY TEMP sensor read controller
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : hygro_read_ctrl.vhd
-- Author     : Jere Nissinen
-- Edited     : 13.10.2026
-------------------------------------------------------------------------------
-- Description: Reads temperature and humidity data from the sensor using the i2c_maseter.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity hygro_read_ctrl is
    generic(
        byte_width_g : integer := 8
    ); 
    port(
        clk, rst_n : in std_logic;
        permission_in : in std_logic; --Tells that this module has permmission to use i2c_master
        byte_done_in : in std_logic; --i2c master tells that a byte has been processed
        byte_in : in std_logic_vector(byte_width_g-1 downto 0);
        trigger_measurement_in : in std_logic; --Triggers the measeurement
        request_permission_out : out std_logic; --Used to request permission to use i2c_master
        start_out : out std_logic; --Initiates the use of i2c_master
        end_out : out std_logic; --Tells the i2c_master that the last byte is being sent
        byte_out : out std_logic_vector(byte_width_g-1 downto 0); --The byte sent through i2c_mater
        temperature_out : out std_logic_vector(2*byte_width_g-1 downto 0);
        humidity_out : out std_logic_vector(2*byte_width_g-1 downto 0)
    );
end hygro_read_ctrl;

architecture rtl of hygro_read_ctrl is 

    --The constant address values the controller has send

    --First it has to send the pointer register 0x00 to the sensor so the measurement starts
    constant i2c_address_write_c : std_logic_vector := "10000000"; --The seven bit address + write bit
    constant pointer_register_address_c : std_logic_vector := "00000000"; --Writing to this address triggers the measurement.
    
    --Then reading from the sensor
    constant i2c_address_read_c : std_logic_vector := "10000001";

    --The states in fsm and state signal
    type state_type is (idle, ask_permission, send_address_write, send_register_address, send_address_read, receive_temp_msb, receive_temp_lsb, receive_hum_msb, receive_hum_lsb);
    signal curr_state_r : state_type;
    
begin
    --The fsm process
    fsm_pcocess : process(clk, rst_n)
    begin
        if(rst_n = '0') then
            request_permission_out <= '0';
            start_out <= '0';
            end_out <= '0';
            byte_out <= (others => '0');
            temperature_out <= (others => '0');
            humidity_out <= (others => '0');
            curr_state_r <= idle;

        elsif(clk'event and clk = '1') then
            
            case curr_state_r is

            when idle =>
                request_permission_out <= '0';
                start_out <= '0';
                end_out <= '0';
                byte_out <= (others => '0');

                --Wait for the triggered measurement:
                if(trigger_measurement_in = '1') then
                    temperature_out <= (others => '0');
                    humidity_out <= (others => '0');
                    curr_state_r <= ask_permission;
                end if;

            when ask_permission =>
                request_permission_out <= '1';
                if(permission_in = '1') then
                    curr_state_r <= send_address_write;
                end if;

            when send_address_write =>
                byte_out <= i2c_address_write_c;
                start_out <= '1';
                if(byte_done_in = '1') then
                    curr_state_r <= send_register_address;
                end if;

            when send_register_address =>
                byte_out <= pointer_register_address_c;
                start_out <= '0';
                end_out <= '1';
                if(byte_done_in = '1') then
                    curr_state_r <= send_address_read;
                end if;

            when send_address_read =>
                byte_out <= i2c_address_read_c;
                start_out <= '1';
                end_out <= '0';
                if(byte_done_in = '1') then
                    curr_state_r <= receive_temp_msb;
                end if;

            when receive_temp_msb =>
                byte_out <= (others => '0');
                start_out <= '0';
                if(byte_done_in = '1') then
                    temperature_out(2*byte_width_g-1 downto byte_width_g) <= byte_in;
                    curr_state_r <= receive_temp_lsb;
                end if;

            when receive_temp_lsb =>
                if(byte_done_in = '1') then
                    temperature_out(byte_width_g-1 downto 0) <= byte_in;
                    curr_state_r <= receive_hum_msb;
                end if;

            when receive_hum_msb =>
                if(byte_done_in = '1') then
                    humidity_out(2*byte_width_g-1 downto byte_width_g) <= byte_in;
                    curr_state_r <= receive_hum_lsb;
                end if;

            when receive_hum_lsb =>
                end_out <= '1';
                if(byte_done_in = '1') then
                    humidity_out(byte_width_g-1 downto 0) <= byte_in;
                    curr_state_r <= idle;
                end if;
                
            end case;
        end if;
    end process fsm_pcocess;

end rtl;