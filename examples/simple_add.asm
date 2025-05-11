; Simple addition program
; Adds two numbers and stores the result

; Load values into registers
ADDI R1, R0, #10   ; R1 = 10
ADDI R2, R0, #20   ; R2 = 20

; Add the values
ADD R3, R1, R2     ; R3 = R1 + R2 = 30

; Store the result to memory
STORE R3, [R0 + 0x10000000]  ; Store at address 0x10000000

; Halt the processor
HALT