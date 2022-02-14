# nexa_parser
Parses Nexa PET-910 remote control payload captured with a logic analyzer from Pulseview .sr file to human readable bits

Payload structure is: 

-250 µs ON, 2550 µs OFF for -1 (initializer bit)
-250 µs ON, 250 µs OFF (or HIGH to LOW and 250 µs pause) for 0
-250 µs ON, 1250 µs OFF (or HIGH to LOW and 1250 µs pause) for 1
