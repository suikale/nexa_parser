# nexa_parser
Parses Nexa PET-910 remote control payload captured with a logic analyzer from Pulseview .sr file to human readable bits

### payload structure: 

    [13 bytes for remote id] [state byte] [group byte] [device id byte]

#### bytes: 

    0101, 0110, 1001, 1010

#### bits:

    -1: 250 µs ON, 2550 µs OFF (init bit) 
     1: 250 µs ON, 1250 µs OFF
     0: 250 µs ON,  250 µs OFF

#### states:
    
    0101: off
    0110: on
    1001: all off
    1010: all on

#### ids and groups
    
    0101: 1
    0110: 2
    1001: 3
    1010: 4
