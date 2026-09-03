# Temporary Demo Student Guide

This guide is for testing the AgPV Assistant during a temporary demo
window. The app is an active research prototype, so the goal is to test the
conversation flow, usefulness of responses, and solar-yield estimate workflow.

## Demo Access

Access code:
```text
purdue_vip
```

## Before You Start

You will need your own Purdue GenAI Studio API key. This is needed because the
assistant uses Purdue GenAI Studio to answer questions and explain simulation
results.

To get an API key:

1. Log in to Purdue GenAI Studio.
2. Open your avatar/profile menu.
3. Go to **Settings**.
4. Go to **Account**.
5. Expand **API Keys**.
6. Create a new API key and copy it.

Instructions to obtain an API Key can be found on the link below:

```text
https://www.rcac.purdue.edu/knowledge/genaistudio/api
```

Treat your API key like a password. Do not share it with anyone, paste it into
public chat, or commit it to GitHub.

If the app asks for an API key:

1. Enter your Purdue GenAI Studio API key.
2. The key is kept only for your current app session.
3. Do not share your API key with anyone else.

If the app does not ask for an API key, the demo host has already configured
one for the app session.

## What The App Does

The AgPV Assistant helps users explore agrivoltaic planning questions.

Current capabilities:

- Collects basic user context, such as role, experience level, project goal,
  and optional site location.
- Answers general agrivoltaics and solar-design questions.
- Uses validated papers retrieval for research-grounded answers when relevant.
- Can run MATLAB/PVMAPS in the background for solar-yield estimates.
- Shows monthly solar-yield results as a chart.
- Keeps the conversation going after an estimate is generated.

## Recommended Test Flow

### 1. Open The App

1. Open the demo URL.
2. Enter the access code if prompted.
3. Enter your Purdue GenAI Studio API key if prompted.
4. Choose a mode.

For most testers, choose:

```text
Guided mode
```

Choose Expert mode only if you want to manually enter PVMAPS parameters.

### 2. Fill The Profile Form

Enter:

- Your user type.
- Your solar-design experience level.
- Your project goal.
- A site location if you want location-specific discussion or a solar-yield
  estimate.
- Optional extra details about your goal.

Example site locations:

```text
Lafayette, Indiana
Pune, India
West Lafayette, Indiana
```
You can add exact locations too.

### 3. Try General AgPV Questions

Example questions:

```text
What is agrivoltaics?
```

```text
How can solar panels affect crop growth?
```

```text
What tradeoffs should a farmer consider before installing solar panels?
```

```text
How does row spacing affect bifacial solar farm yield?
```

### 4. Try A Solar-Yield Estimate

Example requests:

```text
I want a quick solar-yield estimate for my location.
```

```text
Can you estimate solar yield for a 20-acre farm in Lafayette, Indiana?
```

```text
I grow soybeans and want to know if AgPV is feasible. Can you estimate solar yield?
```

The app may run PVMAPS in the background and then show:

- The confirmed location.
- A monthly yield chart.
- A plain-language explanation.

### 5. Ask Follow-Up Questions

After an estimate appears, try questions like:

```text
Why is the summer yield higher than winter?
```

```text
What assumptions did the estimate use?
```

```text
How would changing row spacing affect the result?
```

```text
Is this setup friendly for farm equipment access?
```

## Expert Mode

Expert mode is for users who already understand solar simulation inputs.

Use it if you want to manually enter:

- Site location.
- Panel or module parameters.
- Array configuration.
- Tilt, orientation, pitch, elevation, and related PVMAPS inputs.

The app validates the inputs before running PVMAPS.

## What Feedback To Give

Please submit feedback here:

```text
https://forms.cloud.microsoft/r/gkx03A8BQA
```