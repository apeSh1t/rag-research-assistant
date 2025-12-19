---
title: Dilution Problems
keywords: [dilution, concentration, gradient, samples, solution, buffer, minmix, binary search, remia, MTC]
scenarios:
  - "I need to use a sample with concentration 1 to prepare a solution with concentration 0.3"
  - "How to use one sample and water to prepare multiple solutions with different concentrations?"
  - "Help me generate a dilution plan"
---

# Dilution Problems

## Use Cases
Used when users need to use a single sample (Reagent) and one buffer solution (Buffer, usually water with concentration 0) to prepare one or more target solutions with specific concentrations.

## Definition
Dilution problems involve mixing a high-concentration stock solution (sample) with a zero-concentration solvent (buffer) to achieve one or more lower target concentrations.

- **Input**:
    - 1 sample (Reagent) with known concentration (or default 1).
    - 1 buffer solution (Buffer), usually water with concentration 0.
    - 1 or more target concentrations.
- **Output**:
    - Final mixing plan, i.e., explanation of mixing tree in user-understandable steps, describing how to mix and what the final products look like

---

## Problem Classification and Solution Methods

Dilution problems are mainly divided into two types: single target concentration dilution and multi-target concentration (gradient) dilution.

### 1. Single Target Concentration Dilution

Refers to preparing **one** solution with specific concentration from one sample.

#### Solution Methods

Multiple algorithms can solve this problem:

- **Method 1: Treat as two-component problem using `minmix` algorithm**
  - **Approach**: Treat dilution as a mixing problem with only two liquids (sample and buffer), apply multi-component mixing solution steps.
  - **Steps**:
    1. Calculate required volume ratios of sample and buffer based on target concentration.
    2. Convert this ratio to two integers summing to power of 2.
    3. Call `minmix` algorithm to solve.
    4. Interpret algorithm output mixing tree, generate user-understandable steps.

- **Method 2: Use `binary search` algorithm**
  - **Approach**: This is a fast algorithm specifically designed for dilution problems.
  - **Advantages**: Simple algorithm, fast speed.
  - **Input**: