-------------------------------------------------------------------------------
-- Title      : Stemma soil moisture sensor read controller
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : stemma_read_ctrl.vhd
-- Author     : Jere Nissinen
-- Edited     : 20.10.2026
-------------------------------------------------------------------------------
-- Description: Reads soil moisture from Stemma sensor throuhg i2c
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity stemma_read_ctrl is

    generic(
        byte_width_g : integer := 8
    ); 

    port(
        clk, rst_n : in std_logic;
        permission_in : in std_logic; --Tells that this module has permmission to use i2c_master
        byte_done_in : in std_logic; --i2c master tells that a byte has been processed
        ack_in : in std_logic; --i2c master tells if it got nack
        byte_in : in std_logic_vector(byte_width_g-1 downto 0);
        trigger_measurement_in : in std_logic; --Triggers the measeurement
        request_permission_out : out std_logic; --Used to request permission to use i2c_master
        start_out : out std_logic; --Initiates the use of i2c_master
        end_out : out std_logic; --Tells the i2c_master that the last byte is being sent
        byte_out : out std_logic_vector(byte_width_g-1 downto 0); --The byte sent through i2c_mater
        soil_moisture_out : out std_logic_vector(2*byte_width_g-1 downto 0)
    );

end stemma_read_ctrl;

architecture rtl of stemma_read_ctrl is 

    --The constant address values the controller has send
    constant i2c_address_write_c : std_logic_vector := "01101100"; --The seven bit address + write bit
    constant touch_register_address_c : std_logic_vector := "00001111"; --Touch register address
    constant chn_address_c : std_logic_vector := "00010000";
    --Then reading from the sensor
    constant i2c_address_read_c : std_logic_vector := "01101101";

    --The states in fsm and state signal
    type state_type is (idle, ask_permission, send_address_write, send_touch_register_address, send_chn, wait_state, send_address_read, receive_msb, receive_lsb, retry);
    signal curr_state_r : state_type;

    --Seesaw needs a few ms to process the touch read request (3.2 ms at 125 MHz)
    constant wait_cycles_c : integer := 400000;
    signal wait_counter : integer range 0 to wait_cycles_c;

    

begin

    --The fsm process
    fsm_pcocess : process(clk, rst_n)

    begin

        if(rst_n = '0') then
            request_permission_out <= '0';
            start_out <= '0';
            end_out <= '0';
            byte_out <= (others => '0');
            soil_moisture_out <= (others => '0');
            curr_state_r <= idle;
            wait_counter <= 0;

        elsif(clk'event and clk = '1') then

            case curr_state_r is

            when idle =>
                request_permission_out <= '0';
                start_out <= '0';
                end_out <= '0';
                byte_out <= (others => '0');
                wait_counter <= 0;
                --Wait for the triggered measurement:
                if(trigger_measurement_in = '1') then
                    soil_moisture_out <= (others => '0');
                    curr_state_r <= ask_permission;
                end if;

            when ask_permission =>
                request_permission_out <= '1';
                start_out <= '0';
                end_out <= '0';
                if(permission_in = '1') then
                    curr_state_r <= send_address_write;
                end if;

            when send_address_write =>
                byte_out <= i2c_address_write_c;
                start_out <= '1';
                end_out <= '0';
                --Wait until the address byte has been processed
                if(byte_done_in = '1') then
                    start_out <= '0';
                    --If the sensor acked continue the communication
                    if(ack_in = '0') then
                        curr_state_r <= send_touch_register_address;
                    --If the sensor nacked retry the whole communication
                    else
                        curr_state_r <= retry;
                    end if;
                end if;

            when send_touch_register_address =>
                byte_out <= touch_register_address_c;
                start_out <= '0';
                end_out <= '0';

                --Wait until the touch register address has been processed
                if(byte_done_in = '1') then
                    --If the sensor acked continue the communication
                    if(ack_in = '0') then
                        curr_state_r <= send_chn;
                    --If the sensor nacked retry the whole communication
                    else
                        curr_state_r <= retry;
                    end if;
                end if;

            when send_chn =>
                byte_out <= chn_address_c;
                start_out <= '0';
                end_out <= '1';
                --Wait until the channel address has been processed

                if(byte_done_in = '1') then
                    end_out <= '0';
                    --If the sensor acked wait before reading
                    if(ack_in = '0') then
                        wait_counter <= 0;
                        curr_state_r <= wait_state;
                    --If the sensor nacked retry the whole communication
                    else
                        curr_state_r <= retry;
                    end if;
                end if;





            when wait_state =>
                start_out <= '0';
                end_out <= '0';
                byte_out <= (others => '0');

                --Wait before trying to read the measurement
                if(wait_counter = wait_cycles_c) then
                    curr_state_r <= send_address_read;
                    wait_counter <= 0;
                else
                    wait_counter <= wait_counter + 1;
                end if;
    
            when send_address_read =>
                byte_out <= i2c_address_read_c;
                start_out <= '1';
                end_out <= '0';

                --Wait until the read address has been processed
                if(byte_done_in = '1') then
                    start_out <= '0';
                    --If the sensor acked start receiving the measurement
                    if(ack_in = '0') then
                        curr_state_r <= receive_msb;
                    --If the sensor nacked retry the whole communication
                    else
                        curr_state_r <= retry;
                    end if;
                end if;

            when receive_msb =>
                start_out <= '0';
                end_out <= '0';
                byte_out <= (others => '0');

                --Wait until the first measurement byte has been received
                if(byte_done_in = '1') then
                    soil_moisture_out(2*byte_width_g-1 downto byte_width_g) <= byte_in;
                    curr_state_r <= receive_lsb;
                end if;

            when receive_lsb =>
                start_out <= '0';
                end_out <= '1';
                byte_out <= (others => '0');
                --Wait until the last measurement byte has been received
                if(byte_done_in = '1') then
                    soil_moisture_out(byte_width_g-1 downto 0) <= byte_in;
                    end_out <= '0';
                    curr_state_r <= idle;
                end if;

            when retry =>
                request_permission_out <= '0';
                start_out <= '0';
                end_out <= '0';
                byte_out <= (others => '0');
                wait_counter <= 0;
                curr_state_r <= ask_permission;

            end case;
        end if;
    end process fsm_pcocess;



end rtl;
