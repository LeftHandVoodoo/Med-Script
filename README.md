# Medication Tracking App

This is a PyQt6-based desktop application for tracking medications, providing information about drugs, and checking for contraindications.

## Features

- Add and manage multiple users' medication lists
- Fetch medication information and descriptions using OpenAI's GPT model
- Check for contraindications between medications
- Export medication lists to Excel
- Chat interface for medication-related queries
- Settings menu to configure OpenAI API key

## Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd medication-tracking-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your OpenAI API key:
   - You can set your OpenAI API key directly in the application using the Settings menu.
   - Alternatively, you can create a `.env` file in the project root directory and add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## Usage

Run the main application:

```
python gui/main_window.py
```

- Use the "+" button to add new user tabs
- Add medications using the "Add Medication" button
- Update the database with the "Update Database" button
- Export medications to Excel using the "Export to Excel" button
- Check for contraindications using the "Contraindications" button
- Use the chat interface to ask questions about medications

### Setting up the OpenAI API Key

1. Launch the application
2. Go to the "Settings" menu in the top menu bar
3. Select "Set API Key"
4. Enter your OpenAI API key in the dialog box
5. Click "OK" to save the API key

The API key will be securely stored in a local configuration file and used for all OpenAI API calls.

## File Structure

- `gui/main_window.py`: Main application window and UI logic
- `database/setup.py`: Database setup and connection management
- `api/openai_integration.py`: OpenAI API integration for medication information
- `export/export_to_excel.py`: Excel export functionality
- `tests/test_api.py`: API tests
- `config.py`: Configuration management for API key

## Dependencies

See `requirements.txt` for a full list of dependencies. Main dependencies include:

- PyQt6
- openpyxl
- requests
- python-dotenv (recommended for managing environment variables)

## License

[MIT License](LICENSE)