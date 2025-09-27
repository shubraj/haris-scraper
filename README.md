# Harris County Property Scraper

A comprehensive tool for scraping Harris County instrument data and performing HCAD property searches.

## Features

- **Instrument Scraping**: Scrape instrument data from Harris County Clerk's Office records
- **HCAD Property Search**: Search for property addresses using the Harris County Appraisal District (HCAD) website
- **Data Processing**: Clean and normalize legal descriptions and owner names
- **Export Functionality**: Export results to CSV format
- **User-Friendly Interface**: Streamlit-based web interface

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd harris-scraper
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

## Usage

1. **Run the application**:
   ```bash
   streamlit run app.py
   ```

2. **Step 1 - Scrape Instruments**:
   - Select instrument types from the dropdown
   - Choose date range for the search
   - Click "Start Scraping" to begin data collection
   - Download results as CSV

3. **Step 2 - HCAD Property Search**:
   - Use the scraped data from Step 1
   - Click "Run HCAD Searches" to search for property addresses
   - View and download the final results

## Project Structure

```
harris-scraper/
├── app.py                          # Main application entry point
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── instrument_types.json           # Instrument type mappings
├── apps/                          # Application modules
│   ├── __init__.py
│   ├── instrument_scraper.py      # Instrument scraping app
│   └── hcad_search.py             # HCAD search app
├── scrapers/                      # Web scrapers
│   ├── __init__.py
│   ├── harris_county.py           # Harris County scraper
│   └── hcad.py                    # HCAD scraper
└── utils/                         # Utility functions
    ├── __init__.py
    └── text_processing.py         # Text processing utilities
```

## Configuration

The application uses a centralized configuration system in `config.py`. Key settings include:

- **API Keys**: Set environment variables for external services
- **URLs**: Base URLs for Harris County and HCAD websites
- **Browser Settings**: Number of tabs, headless mode, timeouts
- **File Paths**: Input/output file locations

## Dependencies

- **pandas**: Data manipulation and analysis
- **beautifulsoup4**: HTML parsing
- **requests**: HTTP requests
- **playwright**: Browser automation
- **streamlit**: Web application framework
- **openpyxl**: Excel file handling

## Development

### Code Quality

The project follows Python best practices:

- **Type Hints**: All functions include proper type annotations
- **Docstrings**: Comprehensive documentation for all modules and functions
- **Error Handling**: Robust error handling throughout the codebase
- **Configuration Management**: Centralized configuration system
- **Modular Design**: Clean separation of concerns

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
flake8 .
mypy .
```

## Troubleshooting

### Common Issues

1. **Playwright Installation**: If Playwright fails to install, run `playwright install` manually
2. **Session Cookies**: Harris County cookies may expire and need updating
3. **Rate Limiting**: The scrapers include delays to avoid overwhelming target websites
4. **Memory Usage**: Large datasets may require more memory

### Getting Help

- Check the application logs for error messages
- Ensure all dependencies are properly installed
- Verify that the target websites are accessible

## License

This project is for educational and research purposes. Please respect the terms of service of the websites being scraped.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for complying with the terms of service of the websites being accessed and applicable laws and regulations.