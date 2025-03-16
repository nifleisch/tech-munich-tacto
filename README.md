# Tech:Munich Tacto Challenge

This repository contains the code for the Tech:Munich Tacto Challenge.


## Getting Started

This project uses [Poetry](https://python-poetry.org/) to manage dependencies. Follow these steps to set up the project locally:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/nifleisch/tech-munich-tacto.git
   cd tech-munich-tacto
   ```

2. **Install Dependencies:**

   Install portaudio
   ```bash
   brew install portaudio
   ```

   > If you're on linux or windows, pls research on how to install portaudio 🙏

   Run the following command to create a virtual environment and install all required packages:
   ```bash
   poetry install
   ```

   Refer to the [poetry installation guide](https://python-poetry.org/docs/#installation) if you have poetry not yet installed.

3. **Create your Mistral Agents**

   Refer to the folder `prompts` and for each file in there create an agent in Mistra.
   Have a look at the [mistral website about agents](https://docs.mistral.ai/capabilities/agents/) if you need additional information on how to create agents.

4. **Activate the Virtual Environment:**
   Start the shell within the virtual environment:
   ```bash
   poetry shell
   ```

   Make sure that you export all the environment variables from the `.env`-file.
   ```
   export MISTRAL_API_KEY=<your_api_key>
   export ELEVEN_API_KEY=<your_api_key>

   export LEVERAGE_ANALYZER_AGENT_ID=<agent_id>
   export STRATEGY_FORMALIZER_AGENT_ID=<agent_id>
   export CUSTOMER_EMAIL_AGENT_ID=<agent_id>
   export SUPPLIER_EMAIL_AGENT_ID=<agent_id>

   ```

5. **Run the Application:**
   With the environment activated, you can now run your application. For example:
   ```bash
   python main.py
   ```
   *(Replace `main.py` with the appropriate entry point for your project.)*

6. **Adding New Dependencies:**
   To add additional packages, simply use:
   ```bash
   poetry add <package-name>
   ```

Happy coding!


## Creating the mock dataset

To generate a mock dataset for the project, run the script `dataset/create.py` with the following command:

```bash
python dataset/create.py
```

This will create a mock dataset with 100 events and save it as `dataset/data.csv`. Note that the script will also create the other files in the `dataset` folder that provide further context for the data.
