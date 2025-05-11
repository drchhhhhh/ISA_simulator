; arithmetic_operations.asm
; Demonstrates basic arithmetic operations

; Initialize registers with values
ADDI R1, R0, #5     ; R1 = 5
ADDI R2, R0, #10    ; R2 = 10

; Addition
ADD R3, R1, R2      ; R3 = R1 + R2 = 15

; Subtraction
SUB R4, R2, R1      ; R4 = R2 - R1 = 5

; Multiplication
MUL R5, R1, R2      ; R5 = R1 * R2 = 50

; Division
DIV R6, R5, R2      ; R6 = R5 / R2 = 5

; Store results to memory
STORE R3, [R0 + 0x10000000]  ; Store addition result
STORE R4, [R0 + 0x10000004]  ; Store subtraction result
STORE R5, [R0 + 0x10000008]  ; Store multiplication result
STORE R6, [R0 + 0x1000000C]  ; Store division result

HALT