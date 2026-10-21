-------------------------------------------------------------------------------
-- Title      : I2C arbitter
-- Project    : Spike
-------------------------------------------------------------------------------
-- File       : i2c_arbitter.vhd
-- Author     : Jere Nissinen
-- Edited     : 11.10.2026
-------------------------------------------------------------------------------
-- Description: Implements an i2c arbitter that grants differen resources permissions to
-- use a shared i2c channel. The lowes resource (index 0) is the most important resource and will
-- always be the next in line. Other resources are equal and when they request the permission they
-- will go to the end of the queue. A resource will lift its bit in requests_in port and keep it high until
-- it has finished communicating through i2c. The resource can start the communication once the arbitter
-- responds with putting the resource's index in permissions_out high and keeping it high until the
-- communication is done.
-------------------------------------------------------------------------------
library ieee;
use ieee.std_logic_1164.all;

entity i2c_arbitter is 
    generic(
        num_of_controllers_g : integer := 3
    );
    port(
        clk, rst_n : in std_logic;
        requests_in : in std_logic_vector(num_of_controllers_g-1 downto 0);
        permissions_out : out std_logic_vector(num_of_controllers_g-1 downto 0)
    );
end i2c_arbitter;

architecture rtl of i2c_arbitter is 
    --The queue (Num of controlles is used as an invalid/empty value)
    type queue_type is array (0 to num_of_controllers_g-1) of integer range 0 to num_of_controllers_g;
    signal queue : queue_type;
    signal count : integer range 0 to num_of_controllers_g;
    signal previous_requests_r : std_logic_vector(num_of_controllers_g-1 downto 0);
    
begin

    --Control the queue
    queue_process : process(clk, rst_n)
        variable next_queue : queue_type;
        variable next_count : integer range 0 to num_of_controllers_g;
    begin
        if(rst_n = '0') then
            queue <= (others => num_of_controllers_g);
            count <= 0;
            previous_requests_r <= (others => '0');
        elsif(clk'event and clk = '1') then
            next_queue := queue;
            next_count := count;
            --Remove the current controller once it lowers its request
            if count > 0 then
                if requests_in(queue(0)) = '0' then
                    for i in 0 to num_of_controllers_g-2 loop
                        next_queue(i) := queue(i+1);
                    end loop;
                    next_queue(num_of_controllers_g-1) := num_of_controllers_g;
                    next_count := count - 1;
                end if;
            end if;

            --The most important resource asks for permission it will be added to front
            if(previous_requests_r(0) = '0' and requests_in(0) = '1') then
                if next_count < num_of_controllers_g then
                    if next_count = 0 then
                        next_queue(0) := 0;
                    else
                        --Do not take the bus away from the controller that is already using it: go right behind it
                        for i in num_of_controllers_g-1 downto 2 loop
                            if i <= next_count then
                                next_queue(i) := next_queue(i-1);
                            end if;
                        end loop;
                        next_queue(1) := 0;
                    end if;
                    next_count := next_count + 1;
                end if;
            end if;

            --Other controllers can also be adde
            for i in 1 to num_of_controllers_g-1 loop
                if(previous_requests_r(i) ) = '0' and requests_in(i) = '1' then
                    if next_count < num_of_controllers_g then
                        next_queue(next_count) := i;
                        next_count := next_count + 1;
                    end if;
                end if;
            end loop;

            queue <= next_queue;
            count <= next_count;
            previous_requests_r <= requests_in;
        end if;
    end process queue_process;

    --Give permission to the next in queue
    permission_process : process(queue, count)
    begin
        permissions_out <= (others =>'0');

        if count > 0 then
            permissions_out(queue(0)) <= '1';
        end if;
    end process permission_process;
end rtl;
