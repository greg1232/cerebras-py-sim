# SET_CLK (Set Clock Frequency)

## Description
Sets the core's clock frequency to one of four discrete levels. The desired level is encoded as a 2-bit immediate: BASE (750 MHz), MID (850 MHz), BOOST (1200 MHz), or MAX (1400 MHz). The selected frequency is written to `state->clock_freq`. Use this to trade power for performance, ramping up before compute-heavy regions and back down when idle.

## Behavior
```c
void execute_set_clk(CS3CoreState *state, uint8_t level) {
    switch (level & 0x3) { // 2-bit immediate
        case 0: state->clock_freq = CLK_BASE;  break; // 750 MHz
        case 1: state->clock_freq = CLK_MID;   break; // 850 MHz
        case 2: state->clock_freq = CLK_BOOST; break; // 1200 MHz
        case 3: state->clock_freq = CLK_MAX;   break; // 1400 MHz
    }
}
```
