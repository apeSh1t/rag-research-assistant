---
title: Mixing Tree Understanding
---

# Mixing Tree Understanding

The mixing tree format looks approximately like this:
D1=mix(A(1),B(1)) # represents mixing 1 part A and 1 part B to generate liquid D1
D2=mix(D1(2),B(1)) # represents mixing 2 parts D1 and 1 part B to produce liquid D2

If given input information about what A and B are and their concentrations, we can calculate the concentration of each mixing step (including final solution concentration), making it easy for users to judge correctness.

If no concentration information is provided, just explain each step.