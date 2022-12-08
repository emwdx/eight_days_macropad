# SPDX-FileCopyrightText: original candle code 2017 Mikey Sklar for Adafruit Industries
# Updated code for Wick class implemented on Adafruit Macropad written by Evan Weinberg in December 2022
# SPDX-License-Identifier: MIT

import time

import board
import neopixel
from analogio import AnalogIn
from adafruit_macropad import MacroPad

macropad = MacroPad()

try:
    import urandom as random
except ImportError:
    import random


macropad.pixels.brightness = 0.5
# The LED can be in only one of these states at any given time
bright = 0
up = 1
down = 2
dim = 3
bright_hold = 4
dim_hold = 5

# Percent chance the LED will suddenly fall to minimum brightness
index_bottom_percent = 10
# Absolute minimum red value (green value is a function of red's value)
index_bottom = 128
# Minimum red value during "normal" flickering (not a dramatic change)
index_min = 192
index_max = 255  # Maximum red value

# Decreasing brightness will take place over a number of milliseconds
down_min_msecs = 20
down_max_msecs = 250

# Increasing brightness will take place over a number of milliseconds
up_min_msecs = 20
up_max_msecs = 250

# Percent chance the color will hold unchanged after brightening
bright_hold_percent = 20

# When holding after brightening, hold for a number of milliseconds
bright_hold_min_msecs = 0
bright_hold_max_msecs = 100

# Percent chance the color will hold unchanged after dimming
dim_hold_percent = 5

# When holding after dimming, hold for a number of milliseconds
dim_hold_min_msecs = 0
dim_hold_max_msecs = 50

random.seed(10028)


class Wick():
    
    
    def __init__(self, id):
        self.id = id
        self.isLit = False
        self.index = 0
        self.state = bright
        self.index_start = 255
        self.index_end = 255
        self.flicker_start = 0
        self.flicker_msecs = 0

    def set_color(self,index):
        index = max(min(index, index_max), index_bottom)
        if index >= index_min:
            #strip[0] = [index, int((index * 3) / 8), 0]
            macropad.pixels[self.id] = (index, int((index * 3) / 8), 0)
        elif index < index_min:
            macropad.pixels[self.id] = (index, int((index * 3.25) / 8), 0)

        self.index = index

    def flicker(self):
        current_time = time.monotonic()
        # BRIGHT
        if self.state == bright:
            self.flicker_msecs = random.randint(
                0, down_max_msecs - down_min_msecs) + down_min_msecs
            self.flicker_start = current_time
            self.index_start = self.index_end

            is_index_in_range = self.index_start > index_bottom
            is_random_in_range = random.randint(0, 100) < index_bottom_percent
            if is_index_in_range and is_random_in_range:
                self.index_end = random.randint(
                    0, self.index_start - index_bottom) + index_bottom
            else:
                self.index_end = random.randint(0, self.index_start - index_min) + index_min

            self.state = down

        # DIM
        elif self.state == dim:
            self.flicker_msecs = random.randint(
                0, up_max_msecs - up_min_msecs) + up_min_msecs
            self.flicker_start = current_time
            self.index_start = self.index_end
            self.index_end = random.randint(0, (index_max - self.index_start)) + index_min
            self.state = down

        # DIM_HOLD
        elif self.state == dim_hold:
            # dividing flicker_msecs by 1000 to convert to milliseconds
            if current_time >= (self.flicker_start + (self.flicker_msecs / 1000)):
                if self.state == bright_hold:
                    self.state = bright
                else:
                    self.state = dim

        # DOWN
        elif self.state == down:
            # dividing flicker_msecs by 1000 to convert to milliseconds
            if current_time < (self.flicker_start + (self.flicker_msecs / 1000)):
                index_range = self.index_end - self.index_start
                time_range = (current_time - self.flicker_start) * 1.0

                self.set_color(self.index_start + int(
                    (index_range * (time_range / self.flicker_msecs))))
            else:
                self.set_color(self.index_end)

                if self.state == down:
                    if random.randint(0, 100) < dim_hold_percent:
                        self.flicker_start = current_time

                        dim_max = dim_hold_max_msecs - dim_hold_min_msecs
                        self.flicker_msecs = random.randint(
                            0, dim_max
                        ) + dim_hold_min_msecs
                        self.state = dim_hold
                    else:
                        self.state = dim
                else:
                    if random.randint(0, 100) < bright_hold_percent:
                        self.flicker_start = current_time

                        max_flicker = bright_hold_max_msecs - bright_hold_min_msecs
                        self.flicker_msecs = random.randint(
                            0, max_flicker) + bright_hold_min_msecs
                        self.state = bright_hold
                    else:
                        self.state = bright


                        
wicks = []
for i in range(8):
    wicks.append(Wick(i))

wickDelay = 1.0
currentTime = time.monotonic()
lightTime = currentTime + wickDelay
litIndex = 0
while True:
    currentTime = time.monotonic()
    if(currentTime >= lightTime):
        
        if(litIndex < len(wicks)):
            wicks[litIndex].isLit = True
            litIndex+=1
            lightTime = currentTime + wickDelay
        
        
    for i in range(len(wicks)):
        if(wicks[i].isLit):
            wicks[i].flicker()
    
