---
title: Multi-component Mixing Problems
keywords: [mixing, concentration, multi-component, samples, solution, dilution]
scenarios:
  - "I need to prepare 3ml mixed solution containing 0.2 concentration glucose and 0.1 concentration NaCl, with available 70% glucose and 50% NaCl"
  - "How to mix multiple samples to achieve target concentration?"
discription: Used when users want to mix multiple samples to achieve specific target concentrations.
---

# Multi-component Mixing Problems

## Definition
Prepare mixed solutions containing multiple components, each with specific target concentrations
Input can typically be represented as:
- available_samples: dict, sample name → concentration value; water → 0. Water sample exists even if user doesn't mention it.
- target_concentrations: dict, component name → target concentration value

## Output
- Final mixing plan, explained step-by-step in user-understandable way, describing how to mix and what the final product looks like

## Key Methods
- Minmix for 1:1 mixing scenarios, multi-component mixing algorithm for configuring single composite solutions
    Inputs: Multiple Reagents
    Outputs: Single Composite Reagent
    Optimization: None
    
    Args:
        concentrations: List of concentration values, must be integers, sum to power of 2.
    
    Returns:
        String containing DAG description (FLATFILE format) and DOT format graph description

## Problem Solving Approach
Such problems typically call the Minmix function for solving. Since this function has fixed input/output formats, to achieve ideal solutions, we need to first convert inputs to Minmix function inputs. For example, if input is concentrations, we need to first convert to integer ratios summing to powers of 2, then interpret outputs as human-understandable plans.

## Example Solution Steps
For concentration inputs, the Minmix function solution approach is:
### Step 1: Calculate Mixing Ratios
Based on available sample concentrations and target concentrations, use concentration conservation principles to calculate the ratios each sample should be mixed in.

### Step 2: Normalize Ratios
Check the ratio sum. If certain algorithms require specific formats (e.g., Minmix needs the imput ratio sum to be power of 2), perform conversion. This step will have approximation with a default error tolerance that users can adjust (e.g., increase configuration precision).

### Step 3: Call Mixing Algorithm
Based on the ratios obtained in the previous step, call the mixing algorithm to generate the solution plan and check the plan format.

### Step 4: Mixing Tree Display
Since Minmix outputs a DAG graph, it needs to be converted to mixing tree format for easy understanding and display, providing language feedback to users. After this step, we can wait for user feedback.