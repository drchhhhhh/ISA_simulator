; I/O example program
; Reads input from console, processes it, and outputs result

; Initialize registers
ADDI R1, R0, #0    ; character counter
ADDI R2, R0, #0    ; sum of character values

; Read characters until newline (ASCII 10)
read_loop:
    IO_READ R3, 0   ; Read a character from console
    BEQ R3, R0, read_loop  ; If no character available, try again
    
    ; Check if it's a newline
    ADDI R4, R0, #10  ; ASCII for newline
    BEQ R3, R4, process_input
    
    ; Store the character in memory
    ADDI R5, R0, #0x10001000  ; Base address for input buffer
    ADD R5, R5, R1    ; Address for this character
    STORE R3, [R5]    ; Store the character
    
    ; Update counter and sum
    ADDI R1, R1, #1   ; Increment counter
    ADD R2, R2, R3    ; Add character value to sum
    
    ; Continue reading
    JMP read_loop

; Process the input
process_input:
    ; Calculate average (sum / count)
    BEQ R1, R0, end   ; If count is 0, skip division
    DIV R6, R2, R1    ; R6 = average
    
    ; Output the average as a character
    IO_WRITE R6, 0    ; Write to console
    
    ; Output newline
    ADDI R7, R0, #10  ; ASCII for newline
    IO_WRITE R7, 0    ; Write to console

end:
    HALT              ; Stop execution