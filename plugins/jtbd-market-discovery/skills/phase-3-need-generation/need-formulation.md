Claude: Right! So:
        Step 3: "Plan the stops"
        Step 4: [What about setting the departure time?]

        Do you set departure time in PLAN or was that in UNDERSTAND?

You: Oh, you estimate it in UNDERSTAND, but set it in PLAN

Claude: Exactly! So:
        Step 3: "Plan the stops"
        Step 4: "Set the departure time"

        PLAN phase complete! On to EXECUTE.
```

### EXECUTE Phase

**Guiding Question:** What are the core actions I take to do the job?

```
Claude: Now the EXECUTE phase - the core actions.

        Question: What do you actually do to [GET TO DESTINATIONS ON TIME]?

        This is usually the longest phase (3-5 steps).

        Think about:
        - What are the main activities?
        - What actions take the most time?
        - What are you actively doing vs. waiting?

        What execution steps happen in this phase?
```

**Example Dialogue:**

```
You: You get in the car and drive

Claude: Good start! Let's break that down into discrete steps.

        Before driving, what do you do?
        - Get to the vehicle
        - Prepare the vehicle (unlock, adjust, etc.)

        Then:
        - Drive/travel to destination

        But you also mentioned "stops" in PLAN - do those happen here?

You: Yes, you make the stops during the drive

Claude: Perfect! So EXECUTE steps might be:
        Step 5: "Get to the vehicle"
        Step 6: "Prepare the vehicle"
        Step 7: "Travel to the destination"
        Step 8: "Make planned stops"

        Is that the right sequence? Get to vehicle → Prepare →
        Travel → Make stops along the way?

You: Actually, stops happen during travel, not after

Claude: Right, so maybe:
        Step 5: "Get to the vehicle"
        Step 6: "Prepare the vehicle"
        Step 7: "Travel to the destination"
        Step 8: "Make planned stops" (happens during step 7)

        Or we keep them separate since stops are discrete actions.

        Does this sequence work?

You: Yes, that works

Claude: EXECUTE phase complete! 4 steps, which is typical.
        Now let's assess progress.
```

### ASSESS Phase

**Guiding Question:** How do I evaluate if things are going well?

```
Claude: Now the ASSESS phase - checking progress.

        Question: During or after [GETTING TO DESTINATIONS ON TIME],
        how do you check if you're on track?

        Think about:
        - What indicators do you monitor?
        - What do you measure or verify?
        - How do you know if there's a problem?

        What assessment steps happen in this phase?
```

**Example Dialogue:**

```
You: You check if you're going to arrive on time

Claude: Perfect! Let's make it specific and action-oriented.

        Is it:
        - "Check arrival time"
        - "Monitor progress to destination"
        - "Assess when destination will be reached"

        Which captures the action best?

You: Probably "assess when destination will be reached"

Claude: Excellent! So:
        Step 9: "Assess when the destination will be reached"

        This is an assessment step - evaluating progress.

        Any other things you assess during this job?

You: Not really, that's the main thing

Claude: Makes sense! ASSESS phase: 1 step.
        This phase is often just 1-2 steps.
        Now let's handle adjustments in REVISE.
```

### REVISE Phase

**Guiding Question:** What adjustments might I need to make?

```
Claude: Now the REVISE phase - making adjustments.

        Question: If things aren't going as planned while
        [GETTING TO DESTINATIONS ON TIME], what do you adjust?

        Think about:
        - What changes when assessment reveals issues?
        - What gets corrected or optimized?
        - What adaptations occur mid-job?

        What revision steps happen in this phase?
```

**Example Dialogue:**

```
You: If there's traffic, you change the route

Claude: Perfect! Let's make it general (not just traffic):

        "Change the route as needed"
        "Adjust the route if needed"
        "Reset the route as needed"

        Which ACTION verb works best?

You: "Reset" sounds good

Claude: Great! So:
        Step 10: "Reset the route as needed"

        Any other adjustments that might happen?

You: Maybe adjust departure time for next trip?

Claude: Good thinking, but that sounds like CONCLUDE (learning
        for next time), not REVISE (adjusting during this trip).

        For REVISE, focus on adjustments DURING the current job.
        Route changes are the main revision here.

        REVISE phase: 1 step. Common for REVISE to be 1-2 steps.
        Finally, let's wrap up with CONCLUDE.
```

### CONCLUDE Phase

**Guiding Question:** How do I finalize and wrap up?

```
Claude: Final phase - CONCLUDE.

        Question: Once you arrive, what final steps close out
        the job of [GETTING TO DESTINATIONS ON TIME]?

        Think about:
        - What final actions complete the job?
        - What cleanup or finalization happens?
        - What gets stored or documented for next time?

        What conclusion steps happen in this phase?
```

**Example Dialogue:**

```
You: You park and walk to where you're actually going

Claude: Perfect! Two separate steps:

        Step 11: "Park the vehicle"
        Step 12: "Walk to the destination"

        These are the final actions that complete the job.

        Anything else to conclude? Documentation, for example?

You: Not really for navigation - you're done when you arrive

Claude: Makes sense! Not all jobs have documentation in CONCLUDE.
        For navigation, parking and walking are the final steps.

        CONCLUDE phase: 2 steps. We're done!

        Let's review all 12 steps...
```

---

## Step Validation

After identifying steps, I'll validate them with you:

```
Claude: Let's validate your job steps against quality criteria:

        Your 12 steps for "Get to destinations on time":

        ┌───────────┬────────┬──────────────────────────────────┐
        │ Phase     │ Step # │ Step Name                        │
        ├───────────┼────────┼──────────────────────────────────┤
        │ UNDERSTAND│   1    │ Estimate departure time          │
        │ UNDERSTAND│   2    │ Determine what needs to be prep  │
        │ PLAN      │   3    │ Plan the stops                   │
        │ PLAN      │   4    │ Set the departure time           │
        │ EXECUTE   │   5    │ Get to the vehicle               │
        │ EXECUTE   │   6    │ Prepare the vehicle              │
        │ EXECUTE   │   7    │ Travel to the destination        │
        │ EXECUTE   │   8    │ Make planned stops               │
        │ ASSESS    │   9    │ Assess when destination reached  │
        │ REVISE    │   10   │ Reset the route as needed        │
        │ CONCLUDE  │   11   │ Park the vehicle                 │
        │ CONCLUDE  │   12   │ Walk to the destination          │
        └───────────┴────────┴──────────────────────────────────┘

        Validation Checklist:

        ✅ Specific: Each step is clear and actionable
        ✅ Actionable: All steps describe things that can be done
        ✅ Sequential: Steps follow logical order
        ✅ Necessary: All steps are required (not optional)
        ✅ Phase-appropriate: Each step fits its phase
        ✅ Solution-agnostic: No mention of GPS, maps, apps
        ✅ Consistent granularity: All at same level of detail

        Excellent! These are high-quality job steps.
```

---

## Common Pitfalls and Fixes

I'll help you avoid these mistakes:

### Pitfall 1: Solution-Focused Steps

**Bad:** "Use GPS app to find route"
**Why:** References specific solution (GPS), not stable

**Good:** "Determine optimal route to destination"
**Why:** Outcome-focused, works for any navigation solution

**How I'll catch this:**
```
Claude: Step 4 says "Enter address into GPS"

        ⚠️  This references a specific solution (GPS).

        What's the underlying action, solution-agnostically?
        - "Input destination information"
        - "Specify target location"
        - "Define destination parameters"

        Which works best?
```

### Pitfall 2: Vague Steps

**Bad:** "Do research"
**Why:** Too vague, doesn't specify what research

**Good:** "Identify available options that meet requirements"
**Why:** Specific about what information is being gathered

**How I'll catch this:**
```
Claude: Step 2 says "Prepare for the trip"

        ⚠️  This is too vague. What specifically gets prepared?

        Is it:
        - "Gather required materials for trip"
        - "Verify vehicle readiness"
        - "Determine what needs to be prepared"

        Let's be more specific.
```

### Pitfall 3: Steps Out of Order

**Bad:** Having "Assess results" before "Execute actions"
**Why:** Can't assess before you act

**How I'll catch this:**
```
Claude: You have:
        Step 5: "Assess arrival time"
        Step 6: "Travel to destination"

        ⚠️  Order issue: Can't assess arrival before traveling.

        Should we swap these? Travel first (EXECUTE), then
        assess (ASSESS)?

        Or does assessment happen before travel?
```

### Pitfall 4: Too Granular

**Bad:** "Open vehicle door, Insert key, Turn key, Press brake..."
**Why:** Too detailed, should be one step "Prepare vehicle"

**How I'll catch this:**
```
Claude: You listed:
        - "Unlock car door"
        - "Open car door"
        - "Get in car"
        - "Adjust seat"
        - "Adjust mirrors"
        - "Put on seatbelt"

        ⚠️  Too granular! These are all part of one job step.

        Let's combine as: "Prepare the vehicle"

        This maintains consistent granularity with other steps.
```

### Pitfall 5: Skipping Phases

**Bad:** Only EXECUTE steps, missing UNDERSTAND, PLAN, etc.
**Why:** Incomplete job coverage, will miss customer needs

**How I'll catch this:**
```
Claude: I notice you have 7 steps, all in EXECUTE phase.

        ⚠️  Missing phases: UNDERSTAND, PLAN, ASSESS, REVISE, CONCLUDE

        Let's back up. Before you execute, what information
        do you need? (UNDERSTAND phase)

        We need to cover all 6 phases to avoid missing needs.
```

---

## Refining Step Wording

After initial identification, I'll help refine:

```
Claude: Let's refine the wording for each step.

        Current: "Figure out when to leave"
        Better:  "Estimate departure time"
        Why:     "Figure out" is informal; "estimate" is precise verb

        Current: "Get everything ready"
        Better:  "Determine what needs to be prepared"
        Why:     "Everything ready" is vague; "determine what" is specific

        Current: "Drive to the place"
        Better:  "Travel to the destination"
        Why:     "Drive" is solution-specific; "travel" is general

        Would you like me to suggest refinements for all 12 steps?
```

---

## Customer Validation (Optional)

If you have customer access, I'll provide validation guidance:

### Validation Script

```
Claude: Let's validate the sequence with customers:

        Interview Script:
        "I've broken down [JOB] into these steps. Walk me through
        how YOU do this job and tell me if I'm missing anything."

        [Show them the 12 steps]

        Questions to ask:
        1. "Does this sequence match how you do it?"
        2. "Are there steps I'm missing?"
        3. "Are there steps that don't apply to you?"
        4. "Would you do any of these in a different order?"

        Expected responses:
        ✅ "Yes, that's exactly how I do it"
        ⚠️  "Close, but I do X before Y"
        ❌ "I don't do it that way at all"

        What feedback did you get?
```

### Adjusting Based on Feedback

```
You: Two customers said they check traffic before planning stops

Claude: Excellent feedback! So we need to add a step in UNDERSTAND:

        UNDERSTAND phase:
        1. Estimate departure time
        2. Determine traffic conditions  ← NEW
        3. Determine what needs to be prepared

        Then in PLAN:
        4. Plan the stops (now informed by traffic)
        5. Set the departure time

        Does this better reflect how customers actually do the job?

You: Yes, much better

Claude: Great! Customer validation caught a missing step.
        This is why validation is valuable - reveals gaps.
```

---

## Finalizing Job Steps

After validation and refinement:

```
Claude: Your final job steps for "Get to destinations on time":

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        JOB STEPS MAP (FINAL)
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        Job: "Get to destinations on time"
        Total Steps: 12

        UNDERSTAND Phase (Steps 1-2):
        1. Estimate departure time
        2. Determine what needs to be prepared

        PLAN Phase (Steps 3-4):
        3. Plan the stops
        4. Set the departure time

        EXECUTE Phase (Steps 5-8):
        5. Get to the vehicle
        6. Prepare the vehicle
        7. Travel to the destination
        8. Make planned stops

        ASSESS Phase (Step 9):
        9. Assess when the destination will be reached

        REVISE Phase (Step 10):
        10. Reset the route as needed

        CONCLUDE Phase (Steps 11-12):
        11. Park the vehicle
        12. Walk to the destination

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        ✅ 12 steps (target: 8-15) ✓
        ✅ All 6 phases covered ✓
        ✅ Customer validated ✓
        ✅ Solution-agnostic ✓
        ✅ Consistent granularity ✓

        Excellent job! This job map is ready for Phase 3.
```

---

## Complete Examples

### Example 1: "Get to Destinations On Time" (Navigation)

**12 steps across 6 phases:**

```
┌───────────┬────────┬─────────────────────────────────────────┐
│ Phase     │ Step # │ Step Name                               │
├───────────┼────────┼─────────────────────────────────────────┤
│ UNDERSTAND│   1    │ Estimate departure time                 │
│ UNDERSTAND│   2    │ Determine what needs to be prepared     │
│ PLAN      │   3    │ Plan the stops                          │
│ PLAN      │   4    │ Set the departure time                  │
│ EXECUTE   │   5    │ Get to the vehicle                      │
│ EXECUTE   │   6    │ Prepare the vehicle                     │
│ EXECUTE   │   7    │ Travel to the destination               │
│ EXECUTE   │   8    │ Make planned stops                      │
│ ASSESS    │   9    │ Assess when destination will be reached │
│ REVISE    │  10    │ Reset the route as needed               │
│ CONCLUDE  │  11    │ Park the vehicle                        │
│ CONCLUDE  │  12    │ Walk to the destination                 │
└───────────┴────────┴─────────────────────────────────────────┘
```

**Result:** Foundation for 85 customer needs (7 per step average)

### Example 2: "Ensure Adequate Team Coverage During Absences"

**14 steps across 6 phases:**

```
┌───────────┬────────┬──────────────────────────────────────────┐
│ Phase     │ Step # │ Step Name                                │
├───────────┼────────┼──────────────────────────────────────────┤
│ UNDERSTAND│   1    │ Identify upcoming absence requests       │
│ UNDERSTAND│   2    │ Determine team capacity during absence   │
│ UNDERSTAND│   3    │ Assess criticality of projects           │
│ PLAN      │   4    │ Identify potential backup resources      │
│ PLAN      │   5    │ Create coverage schedule                 │
│ PLAN      │   6    │ Communicate absence to stakeholders      │
│ EXECUTE   │   7    │ Approve absence request                  │
│ EXECUTE   │   8    │ Assign backup resources to critical tasks│
│ EXECUTE   │   9    │ Update project schedules                 │
│ EXECUTE   │  10    │ Monitor coverage effectiveness           │
│ ASSESS    │  11    │ Verify critical tasks are covered        │
│ REVISE    │  12    │ Reassign backup resources if gaps emerge │
│ CONCLUDE  │  13    │ Document coverage effectiveness          │
│ CONCLUDE  │  14    │ Close out the absence request            │
└───────────┴────────┴──────────────────────────────────────────┘
```

**Result:** Foundation for 87 customer needs (6 per step average)

### Example 3: "Maintain Visibility Into Project Progress"

**13 steps across 6 phases:**

```
┌───────────┬────────┬────────────────────────────────────────┐
│ Phase     │ Step # │ Step Name                              │
├───────────┼────────┼────────────────────────────────────────┤
│ UNDERSTAND│   1    │ Identify key project milestones        │
│ UNDERSTAND│   2    │ Determine stakeholder information needs│
│ PLAN      │   3    │ Establish progress tracking mechanisms │
│ PLAN      │   4    │ Define reporting cadence and format    │
│ PLAN      │   5    │ Set up monitoring tools and dashboards │
│ EXECUTE   │   6    │ Collect progress updates from team     │
│ EXECUTE   │   7    │ Update tracking systems with status    │
│ EXECUTE   │   8    │ Analyze progress against plan          │
│ ASSESS    │   9    │ Verify accuracy of reported progress   │
│ ASSESS    │  10    │ Identify potential risks or delays     │
│ REVISE    │  11    │ Adjust tracking approach if needed     │
│ CONCLUDE  │  12    │ Summarize final project outcomes       │
│ CONCLUDE  │  13    │ Archive project data for future use    │
└───────────┴────────┴────────────────────────────────────────┘
```

**Result:** Foundation for 91 customer needs (7 per step average)

---

## What Happens Next

After completing Phase 2, I'll preview Phase 3:

```
Claude: Excellent work! You now have a complete job map with
        12 validated steps.

        In Phase 3 (Need Generation), we'll use these steps to
        create 80-100 customer needs.

        Here's how it works:

        For each step, we'll:
        1. Identify VARIABLES in that step
        2. Combine with ACTIONS (verbs)
        3. Generate 5-10 needs per step

        Example for Step 3 ("Plan the stops"):

        VARIABLES: Sequence, Routes, Times, Parking
        ACTIONS: Determine, Minimize, Reduce

        CUSTOMER NEEDS:
        - Determine optimal sequence of stops
        - Minimize total number of stops needed
        - Determine parking availability at stops
        - Reduce additional time required for stops
        ... (7 needs total for this one step)

        12 steps × 7 needs per step = ~85 needs total

        These needs will be surveyed for importance/satisfaction
        to calculate opportunity scores.

        Ready for Phase 3?
```

---

## Output from Phase 2

At the end of Phase 2, you'll have:

### 1. Complete Job Steps Map

```markdown
Job: "Get to destinations on time"

┌───────────┬────────┬─────────────────────────────────────────┐
│ Phase     │ Step # │ Step Name                               │
├───────────┼────────┼─────────────────────────────────────────┤
│ UNDERSTAND│   1    │ Estimate departure time                 │
│ UNDERSTAND│   2    │ Determine what needs to be prepared     │
│ PLAN      │   3    │ Plan the stops                          │
│ PLAN      │   4    │ Set the departure time                  │
│ EXECUTE   │   5    │ Get to the vehicle                      │
│ EXECUTE   │   6    │ Prepare the vehicle                     │
│ EXECUTE   │   7    │ Travel to the destination               │
│ EXECUTE   │   8    │ Make planned stops                      │
│ ASSESS    │   9    │ Assess when destination will be reached │
│ REVISE    │  10    │ Reset the route as needed               │
│ CONCLUDE  │  11    │ Park the vehicle                        │
│ CONCLUDE  │  12    │ Walk to the destination                 │
└───────────┴────────┴─────────────────────────────────────────┘

Total: 12 steps
Phase Distribution:
- UNDERSTAND: 2 steps
- PLAN: 2 steps
- EXECUTE: 4 steps (most, as expected)
- ASSESS: 1 step
- REVISE: 1 step
- CONCLUDE: 2 steps
```

### 2. Validation Notes

```markdown
Customer Validation Results:

Sample Size: 10 customers
Sequence Match: 90% (9/10 said this matches their process)
Missing Steps: 1 customer suggested adding traffic check (already covered in step 1)
Order Issues: None reported
Feedback: "Very accurate", "This is exactly what I do", "Comprehensive"

Confidence: High - ready for need generation
```

### 3. Job Step Template Export

```markdown
You can export this to the job-steps-worksheet.md template:

File: outputs/navigation-job-steps.md

[Contains the complete job steps table formatted per template]
```

### 4. Foundation for Phase 3

```markdown
Ready for Need Generation:
- 12 steps identified ✓
- All 6 phases covered ✓
- Customer validated ✓
- Solution-agnostic ✓

Expected Output for Phase 3:
- 5-10 needs per step
- ~85 total customer needs
- Organized by job step
- Ready for survey
```

---

## Tips for Success in Phase 2

### Do's

✅ **Cover all 6 phases**
- Even if a phase has just 1 step, include it
- Missing phases means missing customer needs

✅ **Maintain consistent granularity**
- All steps should be at same level of detail
- Not "Travel to destination" alongside "Press accelerator pedal"

✅ **Use action verbs**
- Every step should start with or imply an action
- "Estimate", "Plan", "Travel", "Assess", etc.

✅ **Validate sequence**
- Steps should follow natural order of job execution
- UNDERSTAND before PLAN before EXECUTE

✅ **Stay solution-agnostic**
- No GPS, apps, specific tools
- Focus on the actions, not the solutions

### Don'ts

❌ **Don't skip phases**
- "I don't need UNDERSTAND" → Yes you do, there are needs there
- Every phase has opportunities

❌ **Don't be too granular**
- Aim for 8-15 steps, not 50
- Combine micro-steps into meaningful actions

❌ **Don't be too vague**
- "Do the job" → Not helpful
- "Execute the plan" → Not specific enough

❌ **Don't reference solutions**
- "Use the GPS" → Solution-focused
- "Determine route" → Outcome-focused

❌ **Don't worry about perfection**
- You can refine steps as you generate needs
- Getting 80% right now is better than 100% later

---

## Common Questions

**Q: What if I can't identify 8-15 steps?**

A: If you have <8 steps, you're probably being too high-level. Break steps down more granularly. If you have >15 steps, you're being too detailed or might have multiple jobs bundled.

**Q: What if some phases don't apply to my job?**

A: All jobs have all 6 phases, but some phases may have just 1 step. Don't skip phases - there are always customer needs in every phase.

**Q: Can I have different numbers of steps in each phase?**

A: Yes! EXECUTE typically has the most (3-5). ASSESS and REVISE often have just 1-2. This is normal and expected.

**Q: Should steps be time-based or action-based?**

A: Action-based. "Travel for 30 minutes" is time-based (bad). "Travel to the destination" is action-based (good).

**Q: What if customers do the job differently?**

A: Capture the most common sequence. If segments differ significantly, you may need separate job analyses per segment.

---

## Ready for Phase 3?

Once you have 8-15 validated job steps, we'll move to **Phase 3: Need Generation**.

To continue:

```
> "I'm ready for Phase 3"
```

Or to pause and export your job steps:

```
> "Save my job steps and pause"
```

---

**Phase 2 Complete!**

---

# Phase 3: Customer Need Generation
