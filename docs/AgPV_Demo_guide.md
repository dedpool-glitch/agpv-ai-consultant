# AgPV Assistant Guide

This guide explains how to install the required software, start the AgPV
Assistant, test its main features, and stop it safely.

## System Requirements

You need:

- A Windows computer.
- Internet access.
- MATLAB R2026a.
- Mapping Toolbox for MATLAB R2026a.
- A Purdue GenAI Studio API key.
- The complete `AgPV-Assistant` distribution folder supplied by the project team.

Do not move or share `AgPV-Assistant.exe` by itself. It depends on the
`application` and `_internal` folders distributed with it.

## 1. Install MATLAB

Install MATLAB R2026a using the MathWorks installer and your Purdue-linked
MathWorks account. Use the default installation location when possible:

Official MathWorks installation instructions:

```text
https://www.mathworks.com/help/install/ug/install-products-with-internet-connection.html
```

```text
C:\Program Files\MATLAB\R2026a
```

During installation, select:

- MATLAB
- Mapping Toolbox

Deep Learning Toolbox is optional. It is required only for the
`PVK_SI_2T` and `PVK_SI_4T` cell-technology models; the other PVMAPS cell
technologies do not require it.

If MATLAB R2026a is already installed without Mapping Toolbox, rerun the
MathWorks installer, select the existing R2026a installation, and add Mapping
Toolbox.

To confirm the toolbox is installed, open MATLAB and enter:

```matlab
ver
```

`Mapping Toolbox` should appear in the displayed product list. Close MATLAB
before starting the AgPV Assistant.

## 2. Obtain A Purdue GenAI Studio API Key

1. Log in to Purdue GenAI Studio.
2. Open your profile menu.
3. Select **Settings**.
4. Select **Account**.
5. Expand **API Keys**.
6. Create a key and store it somewhere secure.

Purdue's API instructions are available here:

```text
https://www.rcac.purdue.edu/knowledge/genaistudio/api
```

Treat the API key like a password. Do not share it, include it in submitted
files, or commit it to GitHub. The application asks each user to provide
their own key for the current session.

## 3. Start The Application

1. Extract the complete distribution to a writable location, such as your
   Desktop or Documents folder.
2. Open the extracted `AgPV-Assistant` folder.
3. Double-click `AgPV-Assistant.exe`.
4. Keep the console window open while using the application.
5. Wait for the application to open in your web browser.

If the browser does not open automatically, find the local URL in the console,
typically:

```text
http://localhost:8501
```

Open that address in your browser. The application runs locally on your
computer; closing its console stops it.

## 4. Enter The Application

Enter your Purdue GenAI Studio API key. Then choose one of the two modes:

- **Guided mode** for a conversational workflow.
- **Expert mode** for manually entering PVMAPS simulation parameters.

Use Guided mode unless you need to enter simulation parameters manually.

## 5. Recommended Test Flow

### Create A Profile

Provide your role, solar experience, project goal, and a location. Example
locations include:

```text
Lafayette, Indiana
West Lafayette, Indiana
Pune, India
```

### Ask An Agrivoltaics Question

Try:

```text
How does row spacing affect bifacial solar farm yield?
```

The assistant may retrieve relevant information from its research knowledge
base before answering.

### Request A Solar-Yield Estimate

Try:

```text
I want a quick solar-yield estimate for my location.
```

The application may ask for relevant missing information before running
PVMAPS. A simulation can take approximately one minute. Do not close the
console or submit the request repeatedly while it is running.

After completion, review:

- The confirmed location.
- Configuration and assumptions.
- Monthly and yearly yield results.
- The output explanation.
- Available result downloads.

### Ask A Follow-Up

Try:

```text
What assumptions were used in this estimate?
```

```text
Why is summer yield higher than winter yield?
```

```text
Was the selected row spacing optimized or assumed?
```

## 6. Expert Mode

Expert mode allows experienced users to enter site, module, array, and
simulation parameters directly. The application validates these inputs before
running PVMAPS.

Keep **Maximum Parallel Workers** set to `0` unless you specifically need to
test parallel execution. Parallel execution may require an
additional MATLAB toolbox.

## 7. Stop The Application

Return to the console window and press:

```text
Ctrl+C
```

Wait for the server to stop, then close the console and browser tab. Do not
leave multiple copies of the application running.

## Troubleshooting

### The Browser Is Blank Or Does Not Open

- Wait for the local URL to appear in the console.
- Open `http://localhost:8501` manually.
- Keep the console open and check it for an error message.
- Stop and restart the application if the server exited.

### The MATLAB Worker Fails

Confirm that MATLAB R2026a and Mapping Toolbox are installed. Close any open
MATLAB sessions, restart the application, and try once more.

If the error mentions `timezone` or Mapping Toolbox, Mapping Toolbox is missing
or unavailable under your license.

### The API Key Is Rejected

Create a new Purdue GenAI Studio API key and enter it without extra spaces. Do
not use someone else's key.

### Responses Are Slow

GenAI Studio requests and MATLAB simulations can take time. Wait for the current
request to finish rather than submitting it repeatedly. If an API request times
out, wait briefly and try again.

### Windows Blocks The Application

Do not bypass security warnings for a package obtained from an unknown source.
Confirm that you received the folder through an official project channel,
then contact the project team if Windows still blocks it.

When reporting a problem, include a screenshot of the browser and the complete
error shown in the console. Never include your API key.

## Data And Privacy

This is a research prototype. Do not enter passwords, confidential project
information, personal records, or other sensitive data. Simulation outputs and
application logs may be saved inside the local distribution folder.

## Feedback

Submit feedback using this form:

```text
https://forms.cloud.microsoft/r/gkx03A8BQA
```
