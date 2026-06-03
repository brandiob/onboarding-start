module spi_peripheral(
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

    reg copi_temp0;
    reg copi_temp1;

    reg ncs_temp0;
    reg ncs_temp1;

    reg sclk_temp0;
    reg sclk_temp1;
    reg sclk_temp2;

    wire rw_bit;
    wire [6:0] address;
    wire [7:0] payload;

    reg transaction_active;
    reg transaction_ready;

    reg [15:0] shift_reg;
    reg [4:0] bit_count;

    // continous parser ensures values are instantly readable as shift_reg changes
    assign rw_bit  = shift_reg[15];
    assign address = shift_reg[14:8];
    assign payload = shift_reg[7:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            copi_temp0 <= 1'b0;
            copi_temp1 <= 1'b0;

            ncs_temp0 <= 1'b1;
            ncs_temp1 <= 1'b1;

            sclk_temp0 <= 1'b0;
            sclk_temp1 <= 1'b0;
            sclk_temp2 <= 1'b0;

            transaction_active <= 1'b0;
            transaction_ready <= 1'b0;

            shift_reg <= 16'b0;
            bit_count <= 5'b0;

            en_reg_out_7_0  <= 8'h00;
            en_reg_out_15_8 <= 8'h00;
            en_reg_pwm_7_0  <= 8'h00;
            en_reg_pwm_15_8 <= 8'h00;
            pwm_duty_cycle  <= 8'h00;
        end else begin
            // sync inputs
            copi_temp1 <= copi_temp0;
            copi_temp0 <= COPI;

            ncs_temp1 <= ncs_temp0;
            ncs_temp0 <= nCS;

            sclk_temp2 <= sclk_temp1;
            sclk_temp1 <= sclk_temp0;
            sclk_temp0 <= SCLK;

            // process write command when nCS goes high
            if (ncs_temp0 == 1'b1 && ncs_temp1 == 1'b0) begin
                if (rw_bit == 1'b1 && address <= 7'h04 && bit_count == 5'd16) begin
                    case (address)
                        7'h00: en_reg_out_7_0  <= payload;
                        7'h01: en_reg_out_15_8 <= payload;
                        7'h02: en_reg_pwm_7_0  <= payload;
                        7'h03: en_reg_pwm_15_8 <= payload;
                        7'h04: pwm_duty_cycle  <= payload;
                        default: ; // handle CASEINCOMPLETE
                    endcase
                end
            end

            // clear or shift data
            if (ncs_temp0 == 1'b1) begin
                bit_count <= 5'b0;
                transaction_active <= 1'b0;
                transaction_ready  <= 1'b0;
                shift_reg <= 16'b0;
            end else begin
                transaction_active <= 1'b1;
                if (sclk_temp1 == 1'b1 && sclk_temp2 == 1'b0) begin // rising edge of SCLK
                    shift_reg <= {shift_reg[14:0], copi_temp1};
                    bit_count <= bit_count + 1'b1;
                end
            end 
        end
    end

    wire _unused_signals = &{transaction_active, transaction_ready, 1'b0};

endmodule