---
title: RGB to CMY Color Space Conversion
---

# RGB to CMY Color Space Conversion

## Definition
Convert RGB color model to CMY color model

## Conversion Formula
- C = 255 - R
- M = 255 - G
- Y = 255 - B

## Input
- rgb: [R, G, B], range 0-255

## Output
- C: float, range 0-255
- M: float, range 0-255
- Y: float, range 0-255

## Example
Input: RGB(128, 20, 190)
Output: C=128, M=235, Y=60

## Solution Method
Calculate directly according to the formula. No external tools needed.