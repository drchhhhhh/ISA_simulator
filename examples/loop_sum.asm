; Loop sum program
; Calculates the sum of numbers from 1 to 10

; Initialize registers
ADDI R1, R0, #1    ; counter = 1
ADDI R2, R0, #0    ; sum = 0
ADDI R3, R0, #10   ; limit = 10

; Loop to calculate sum
loop:
    ADD R2, R2, R1     ; sum += counter
    ADDI R1, R1, #1    ; counter++
    BEQ R1, R3, check  ; if counter == limit, goto check
    JMP loop           ; else continue loop

; Check if we've reached the end
check:
    ADD R2, R2, R1     ; add final number (10)
    STORE R2, [R0 + 0x10000000]  ; store result to memory
    HALT               ; stop execution