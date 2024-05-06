# Home Assistant Dashboard Setup

This guide explains how to set up a dashboard in Home Assistant using a YAML configuration file.

## Prerequisites

- **Home Assistant**: Ensure you have Home Assistant installed and running.

## Getting Started


1. **Access Home Assistant**

   Open Home Assistant in a web browser.

2. **Navigate to Lovelace Dashboard**

   - Click on "Settings" in the sidebar.
   - Click on "Dashboards".
   - Click "Add Dashboard".
   - Select "New Dashboard" and give it a name.

3. **Prepare and Execute Script to Generate YAML Configuration**

   Before importing the YAML configuration into Home Assistant, you can generate a custom YAML configuration using a script. Follow these steps:
   #### Linux Users

   Before proceeding, you need to prepare and execute the script `generate_yaml.sh` which will generate the necessary YAML configuration for your dashboard. Follow these steps:

   - **Make the Script Executable**:  
     Open a terminal or command prompt and navigate to the location of `generate_yaml.sh`. Run the following command to make the script executable:
     ```bash
     chmod +x generate_yaml.sh
     ```

   - **Run the Script**:  
     Execute the script by typing the following command in the terminal:
     ```bash
     ./generate_yaml.sh
     ```
     This script will prompt you to enter a name for the dashboard (use underscores for spaces), and then it will generate a YAML configuration file named `<custom_name>.yaml`.

    

   #### Windows Users

   - Open PowerShell.
   - Navigate to the directory where your script `generate_yaml.ps1` is located.
   - Run the script by entering its name 
      ```bash
      .\generate_yaml.ps1`
      ```
   - Follow the prompts to enter a custom name for your dashboard.
   - The script will generate a YAML file named `<custom_name>.yaml` in the same directory.
   
4. **Import YAML Configuration into Home Assistant**

   - Copy the content of the generated YAML file (`<custom_name>.yaml`).
   - Return to the Home Assistant dashboard.
   - Click on "Configuration" and select "YAML Configuration".
   - Paste the copied YAML configuration into the editor.
   - Click "Save" to apply the changes.

5. **View Your Dashboard**

   Return to the Home Assistant dashboard to view and interact with your newly configured dashboard.

## Additional Information

- For more detailed information on configuring dashboards in Home Assistant, refer to the [official Home Assistant documentation](https://www.home-assistant.io/docs/frontend/lovelace/).

