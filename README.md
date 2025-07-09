# Restaurant Data Scraper

This project is a Python-based web scraper that collects restaurant data and reviews from Google Maps using Playwright. The scraper extracts details such as restaurant name, category, price range, address, website, phone number, coordinates, and reviews (including language and ratings).

## Features

- Scrapes restaurant listings and detailed information from Google Maps.
- Extracts and saves reviews, including language detection and photo count.
- Outputs data as CSV files for each coordinate searched.
- Handles retries and basic anti-bot measures.

## Requirements

- Python 3.8+
- [Playwright](https://playwright.dev/python/)
- [playwright-stealth](https://github.com/AtuboDad/playwright-stealth)
- pandas

Install dependencies:
```sh
pip install playwright pandas playwright-stealth
playwright install
```

## Usage

1. **Prepare Input Files:**
   - `coordinates.txt`: List of Google Maps coordinates (one per line) to scrape.
   - Optionally, `input.txt`: List of search keywords (one per line) if not using the `-s` argument.

2. **Run the Scraper:**
   ```sh
   python res_scrape.py -t 100  # Scrape up to 100 restaurants per coordinate
   ```
   - Use `-s` to specify a search keyword (default is "restaurant").
   - Use `-t` to specify the maximum number of restaurants to scrape per coordinate.

3. **Output:**
   - CSV files are saved in the `output/` directory, named after each coordinate.

## File Structure

- [`res_scrape.py`](restaurant_data/data_scraper/res_scrape.py): Main scraping script.
- `coordinates.txt`: Input file with coordinates.
- `output/`: Directory where CSV files are saved.

## Notes

- The script launches a visible browser window by default (`headless=False`). Change to `True` for headless operation.
- Make sure your Google Maps URLs/coordinates are valid.
- Use responsibly and respect Google Maps' terms of service.

## License

MIT License
