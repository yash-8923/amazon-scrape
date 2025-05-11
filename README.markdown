# Amazon Soft Toys Scraper and Analyzer

This project is a Python-based web scraper that extracts non-sponsored, non-Amazon's Choice soft toy products from Amazon.in, performs data analysis, and saves the results in a structured format. The script scrapes product details, cleans the data, generates visualizations, and saves the analysis output to an Excel file.

## Features

- Scrapes up to 20 non-sponsored, non-Amazon's Choice soft toy products from Amazon.in.
- Extracts product details: title, brand, price, rating, reviews, image URL, and product URL.
- Performs three types of analysis:
  - **Brand Performance**: Top brands by frequency, average rating by brand, and high-rated but less frequent brands.
  - **Price vs. Rating**: Average price by rating range, high-value products, and overpriced products.
  - **Review & Rating Distribution**: Top products by reviews and rating, and highly rated but less reviewed products.
- Saves raw data to a CSV file (e.g., `amazon_soft_toys_20250511_172345.csv`).
- Saves analysis results to an Excel file (`analysis_results.xlsx`) with separate sheets for each analysis.
- Generates essential visualizations as PNG files.

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- ScraperAPI account (free tier available)

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/amazon-soft-toys-scraper.git
   cd amazon-soft-toys-scraper
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install requests beautifulsoup4 selenium pandas numpy matplotlib seaborn webdriver-manager tenacity openpyxl
   ```

4. **Set Up ScraperAPI Key**:
   - Sign up for a free account at [ScraperAPI](https://www.scraperapi.com/).
   - Set your API key as an environment variable:
     ```bash
     export SCRAPERAPI_KEY='your-scraperapi-key'
     ```
     On Windows:
     ```bash
     set SCRAPERAPI_KEY=your-scraperapi-key
     ```

5. **Install Google Chrome**:
   - Ensure Google Chrome is installed on your system, as the script uses ChromeDriver for web scraping.

## Usage

1. **Run the Script**:
   ```bash
   python amazon_soft_toys_scraper_analyzer_v8.py
   ```

2. **Output Files**:
   - **Raw Data**: Saved as a CSV file (e.g., `amazon_soft_toys_20250511_172345.csv`).
   - **Analysis Results**: Saved as an Excel file (`analysis_results.xlsx`) with three sheets:
     - `Brand Performance`
     - `Price vs Rating`
     - `Review & Rating`
   - **Visualizations**:
     - `top_5_brands_frequency.png`: Bar chart of top 5 brands by frequency.
     - `avg_price_by_rating_range.png`: Bar chart of average price by rating range.
     - `top_5_reviews.png`: Bar chart of top 5 products by number of reviews.
     - `top_5_ratings.png`: Bar chart of top 5 products by rating.

## Project Structure

```
amazon-soft-toys-scraper/
├── amazon_soft_toys_scraper_analyzer_v8.py  # Main script
├── README.md                                # Project documentation
├── .gitignore                               # Git ignore file
├── amazon_soft_toys_*.csv                   # Raw data output (generated)
├── analysis_results.xlsx                    # Analysis output (generated)
├── top_5_brands_frequency.png               # Visualization output (generated)
├── avg_price_by_rating_range.png            # Visualization output (generated)
├── top_5_reviews.png                        # Visualization output (generated)
├── top_5_ratings.png                        # Visualization output (generated)
└── venv/                                    # Virtual environment (optional)
```

## Troubleshooting

- **Titles or Brands Not Extracted Correctly**:
  - The script may fail to extract titles or brands if Amazon.in's HTML structure changes.
  - To debug, add `logger.debug(f"Product HTML: {product.prettify()[:1000]}...")` in the `scrape_amazon_products` function, set the logging level to `DEBUG`, and inspect the HTML to update selectors.

- **Permission Denied Error**:
  - Ensure output files (e.g., `analysis_results.xlsx`) are not open in another application.
  - The script automatically saves raw data with a timestamp to avoid conflicts (e.g., `amazon_soft_toys_20250511_172345.csv`).

- **CAPTCHA Issues**:
  - If a CAPTCHA is detected, consider upgrading your ScraperAPI plan or reducing the scraping frequency.

## Contributing

Feel free to fork this repository, make improvements, and submit pull requests. For major changes, please open an issue first to discuss your ideas.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with Python, Selenium, and Pandas.
- Uses ScraperAPI to handle web scraping challenges.