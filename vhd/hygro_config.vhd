-------------------------------------------------------------------------------
-- Title      : HYGRO HUMIDITY TEMP SENSOR configurator
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : hygro_config.vhd
-- Author     : Jere Nissinen
-- Edited     : 12.10.2026
-------------------------------------------------------------------------------
-- Description: Configurates the HYGRO HUMIDITY TEMP SENSOR before using it to read 
-- data. Sends the config values after reset and then idles around. This has the highest
-- priority to use the i2c_master so it is placed in index 0 in the permission wire.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity hygro_config is
    generic(
        byte_width_g : integer := 8
    ); 
    port(
        clk, rst_n : in std_logic;
        permission_in : in std_logic; --Tells that this module has permmission to use i2c_master
        byte_done_in : in std_logic; --i2c master tells that a byte has been processed
        request_permission_out : out std_logic; --Used to request permission to use i2c_master
        start_out : out std_logic; --Initiates the use of i2c_master
        end_out : out std_logic; --Tells the i2c_master that the last byte is being sent
        byte_out : out std_logic_vector(byte_width_g-1 downto 0) --The byte sent through i2c_mater
    );
end hygro_config;

architecture rtl of hygro_config is 

    --The constant configuration values this sends.
    constant i2c_address_c : std_logic_vector := "10000000"; --The seven bit i2c address + w bit (0)
    constant register_address_c : std_logic_vector := "00000010"; --The reg address where the config parameteres are sent to (0x02)
    constant msb_byte_c : std_logic_vector := "00010000"; --The msb byte of config values
    constant lsb_byte_c : std_logic_vector := "00000000"; --The lsb byte of config values

    --The states in fsm and state signal
    type state_type is (start_state, ask_permission, send_address, send_register_address, send_config_msb, send_config_lsb, done);
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
            curr_state_r <= start_state;

        elsif(clk'event and clk = '1') then
            
            case curr_state_r is

            when start_state =>
                curr_state_r <= ask_permission;

            when ask_permission =>
                request_permission_out <= '1';
                if(permission_in = '1') then
                    curr_state_r <= send_address;
                end if;
            
            when send_address =>
                byte_out <= i2c_address_c;
                start_out <= '1';
                if(byte_done_in = '1') then
                    curr_state_r <= send_register_address;
                end if;
            
            when send_register_address =>
                byte_out <= register_address_c;
                start_out <= '0';
                if(byte_done_in = '1') then
                    curr_state_r <= send_config_msb;
                end if;
            
            when send_config_msb =>
                byte_out <= msb_byte_c;
                if(byte_done_in = '1') then
                    curr_state_r <= send_config_lsb;
                end if;
            
            when send_config_lsb =>
                end_out <= '1';
                byte_out <= lsb_byte_c;
                if(byte_done_in = '1') then
                    curr_state_r <= done;
                end if;

            when done =>
                request_permission_out <= '0';
                start_out <= '0';
                end_out <= '0';
                byte_out <= (others => '0');
            
            end case;
        end if;
    end process fsm_pcocess;

end rtl;