# RoleFit Pro Agent Deployment Guide

This guide explains how to deploy the RoleFit Pro Hardware Agent to a target Windows machine.

## Prerequisites

1.  **Python 3.8+**: Must be installed on the target machine.
    - Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    - **Important**: During installation, check "Add Python to PATH".

2.  **Network Access**: The target machine must be able to reach the RoleFit Pro Server (e.g., `http://192.168.1.100:8000`).

## Installation Steps

1.  **Copy Files**: Copy the entire `agent` folder to the target machine (e.g., `C:\RoleFitAgent`).

2.  **Run Deployment Script**:
    - Open PowerShell as Administrator (optional but recommended).
    - Navigate to the agent folder: `cd C:\RoleFitAgent`
    - Run the deployment script: `.\deploy.ps1`
    - Follow the prompts to enter the Server URL.

3.  **Start Agent**:
    - Double-click `start_agent.bat` in the agent folder.
    - A command window will open showing the agent status.

## Troubleshooting

-   **"Python not found"**: Ensure Python is installed and added to the system PATH. You may need to restart the terminal or computer after installing Python.
-   **"Execution Policy"**: If PowerShell blocks the script, run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell.
-   **Connection Error**: Check if the Server URL is correct and accessible from the target machine. Verify firewall settings on both the server and agent machine.

## Configuration

The server URL is stored in `config.json` and used by `start_agent.bat`. To change it:
1.  Edit `config.json` manually.
2.  Or re-run `.\deploy.ps1`.
