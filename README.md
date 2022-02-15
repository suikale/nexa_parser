# nexa_parser
Parses Nexa PET-910 remote control payload captured with a logic analyzer from Pulseview .sr file to human readable bits

### payload structure: 

    [init bit] 1001 [7 bytes] 0101 [3 bytes] 1001 [state byte] 0101 [id byte]

#### bytes: 

    0101, 0110, 1001 1010

#### bits:

    -1: 250 µs ON, 2550 µs OFF (init bit) 

    1: 250 µs ON, 1250 µs OFF
    
    0: 250 µs ON,  250 µs OFF

#### states:
    
    0101: off
    
    0110: on
    
    1001: all off
    
    1010: all on?

#### id:
    
    0101: 1
    
    0110: 2
    
    1001: 3
    
    1010: 4?

#### group:
    
    ???
