module tt_um_uwasic_onboarding_brandon_thomas(
    input wire COPI,
    input wire SCLK,
    input wire nCS,
    input wire clk,
    input wire rst_n,
    
    output reg [7:0] en_reg_out_7_0,
    output reg [7:0] en_reg_out_15_8,
    output reg [7:0] en_reg_pwm_7_0,    
    output reg [7:0] en_reg_pwm_15_8,
    output reg [7:0] pwm_duty_cycle

);

//declarations

    reg copi_temp0;
    reg copi_temp1;

    reg ncs_temp0;
    reg ncs_temp1;
    reg ncs_temp2;

    reg sclk_temp0;
    reg sclk_temp1;
    reg sclk_temp2;

    reg rw_bit;
    reg [6:0] address;
    reg [7:0] payload;

    reg transaction_active;
    reg transaction_ready;

    reg [15:0] shift_reg;
    reg [4:0] bit_count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin //reseter
            copi_temp0 <= 1'b0;
            copi_temp1 <= 1'b0;

            ncs_temp0 <= 1'b1;
            ncs_temp1 <= 1'b1;
            ncs_temp2 <= 1'b1;

            sclk_temp0 <= 1'b0;
            sclk_temp1 <= 1'b0;
            sclk_temp2 <= 1'b0;

            rw_bit <= 1'b0;
            address <= 7'b0;
            payload <= 8'b0;

            transaction_active <= 1'b0;
            transaction_ready <= 1'b0;

            shift_reg <= 16'b0;
            bit_count <= 5'b0;

            en_reg_out_7_0  <= 8'h00;
            en_reg_out_15_8 <= 8'h00;
            en_reg_pwm_7_0  <= 8'h00;
            en_reg_pwm_15_8 <= 8'h00;
            pwm_duty_cycle  <= 8'h00;
        end else begin //shift
                copi_temp1 <= copi_temp0;
                copi_temp0 <= COPI;

                ncs_temp1 <= ncs_temp0;
                ncs_temp0 <= nCS;

                sclk_temp2 <= sclk_temp1;
                sclk_temp1 <= sclk_temp0;
                sclk_temp0 <= SCLK;

            if (ncs_temp1 == 1'b1) begin //if communication line idle
                bit_count <= 5'b0;
                transaction_active <= 1'b0;
                shift_reg <= 16'b0;
            end else begin
                transaction_active <= 1'b1;
                if (sclk_temp1 == 1'b1 && sclk_temp2 == 1'b0) begin //if sought clock edge
                    shift_reg <= {shift_reg[14:0], copi_temp1};
                    bit_count <= bit_count + 1'b1;
                end
                if (bit_count == 5'd16) begin //if count full
                    rw_bit <= shift_reg[15];
                    address <= shift_reg[14:8];
                    payload <= shift_reg[7:0];   
                end
            end 
                if (ncs_temp1 == 1'b1 && ncs_temp2 == 1'b0) begin
                    // if write command and address valid
                    if (rw_bit == 1'b1 && address <= 7'h04) begin
                        case (address)
                            7'h00: en_reg_out_7_0  <= payload;
                            7'h01: en_reg_out_15_8 <= payload;
                            7'h02: en_reg_pwm_7_0  <= payload;
                            7'h03: en_reg_pwm_15_8 <= payload;
                            7'h04: pwm_duty_cycle  <= payload;
                        endcase
                    end
                end
        end
    end