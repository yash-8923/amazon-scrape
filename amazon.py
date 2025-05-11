import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import random
import os
import logging
from datetime import datetime
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential
from urllib.parse import quote

# Suppress WebDriver manager logs
logging.getLogger('WDM').setLevel(logging.NOTSET)

# Set up script logging (minimal output)
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Environment variable setup
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
if not SCRAPERAPI_KEY:
    raise ValueError("Please set SCRAPERAPI_KEY environment variable.")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=20))
def fetch_page(driver, url: str) -> str:
    """Fetch page content using ScraperAPI and Selenium."""
    api_url = f"http://api.scraperapi.com?api_key={SCRAPERAPI_KEY}&url={quote(url)}"
    driver.get(api_url)
    # Scroll incrementally to ensure all elements load
    for i in range(3):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
        time.sleep(1)
    time.sleep(random.uniform(5, 8))  # Wait for JavaScript rendering
    page_source = driver.page_source
    if "captcha" in page_source.lower():
        raise Exception("CAPTCHA detected")
    return page_source

def setup_selenium() -> webdriver.Chrome:
    """Set up headless Chrome driver for Selenium with additional options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--log-level=3")  # Suppress DevTools messages
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Suppress additional logs
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def scrape_amazon_products(max_products: int = 20, max_pages: int = 3) -> List[Dict]:
    """Scrape non-sponsored, non-Amazon's Choice products for 'soft toys' from Amazon.in."""
    base_url = "https://www.amazon.in/s?k=soft+toys"
    driver = setup_selenium()
    product_data = []
    
    try:
        for page in range(1, max_pages + 1):
            if len(product_data) >= max_products:
                break
            url = base_url if page == 1 else f"{base_url}&page={page}"
            
            html_content = fetch_page(driver, url)
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Find all product containers
            products = soup.find_all("div", {"data-component-type": "s-search-result"})
            if not products:
                break
            
            for product in products:
                if len(product_data) >= max_products:
                    break
                
                # Skip sponsored products
                sponsored_tag = product.find("span", class_="a-color-base", string=lambda text: "Sponsored" in text if text else False)
                if sponsored_tag:
                    continue
                
                # Skip Amazon's Choice products
                amazons_choice_tag = product.find("span", string=lambda text: "Amazon's Choice" in text if text else False)
                if amazons_choice_tag:
                    continue
                
                try:
                    # Extract title with updated selectors
                    title = "N/A"
                    # Try more specific selector
                    title_tag = product.find("span", class_="a-size-medium a-text-normal")
                    if title_tag:
                        title = title_tag.text.strip()
                    else:
                        # Fallback: Look for h2 with span
                        title_tag = product.find("h2", class_="a-size-mini")
                        if title_tag:
                            title_span = title_tag.find("span")
                            if title_span:
                                title = title_span.text.strip()
                        if title == "N/A":
                            # Last resort: Any h2 or span with text
                            title_tag = product.find("h2")
                            if title_tag:
                                title = title_tag.text.strip()
                    
                    # Extract brand with improved logic
                    brand = "Unknown"
                    # Look for brand in a span, excluding "bought in past month"
                    brand_tag = product.find("span", class_="a-size-base a-color-secondary", string=lambda text: "bought" not in text.lower() if text else True)
                    if brand_tag:
                        brand = brand_tag.text.strip()
                    else:
                        # Fallback: Try another class
                        brand_tag = product.find("span", class_="a-size-base", string=lambda text: "bought" not in text.lower() if text else True)
                        if brand_tag:
                            brand_text = brand_tag.text.strip()
                            # Additional check to avoid non-brand text
                            if not any(word in brand_text.lower() for word in ["deal", "limited", "offer"]):
                                brand = brand_text
                        if brand == "Unknown" and title != "N/A":
                            # Extract brand from title
                            words = title.split()
                            if words:
                                brand = words[0]
                                known_brands = ["AURORA", "Jellycat", "Keel", "Gund", "Wild Republic", "Disney", "Barbie", "Fisher-Price", "Melissa & Doug", "Ty", "Squishmallows", "Hasbro", "Mattel", "Aurora", "Nici", "Pusheen"]
                                for word in words:
                                    if word in known_brands:
                                        brand = word
                                        break
                                # Look for "by [Brand]" pattern
                                if " by " in title.lower():
                                    by_index = title.lower().index(" by ") + 4
                                    brand = title[by_index:].split()[0]
                    
                    # Extract price
                    price_tag = product.find("span", class_="a-price")
                    price = price_tag.find("span", class_="a-offscreen").text.strip() if price_tag else "N/A"
                    
                    # Extract rating
                    rating_tag = product.find("span", class_="a-icon-alt")
                    rating = rating_tag.text.strip().split()[0] if rating_tag else "N/A"
                    
                    # Extract number of reviews
                    reviews_tag = product.find("span", class_="a-size-base s-underline-text")
                    reviews = reviews_tag.text.strip().replace(",", "") if reviews_tag else "0"
                    
                    # Extract image URL
                    image_tag = product.find("img", class_="s-image")
                    image_url = image_tag["src"] if image_tag and "src" in image_tag.attrs else "N/A"
                    
                    # Extract product URL
                    link_tag = product.find("a", class_="a-link-normal s-no-outline")
                    product_url = "https://www.amazon.in" + link_tag["href"] if link_tag else "N/A"
                    
                    product_data.append({
                        "title": title,
                        "brand": brand,
                        "price": price,
                        "rating": rating,
                        "reviews": reviews,
                        "image_url": image_url,
                        "product_url": product_url
                    })
                except AttributeError as e:
                    continue
                
                time.sleep(random.uniform(0.5, 1.5))
        
        return product_data
    finally:
        driver.quit()

def clean_data(data: List[Dict]) -> pd.DataFrame:
    """Clean and prepare the scraped data."""
    df = pd.DataFrame(data)
    
    # Remove duplicates based on product_url
    df.drop_duplicates(subset=["product_url"], keep="first", inplace=True)
    
    # Clean price: Remove ₹ and convert to float
    df["price"] = df["price"].apply(lambda x: float(x.replace("₹", "").replace(",", "")) if x != "N/A" else 0.0)
    
    # Clean rating: Convert to float
    df["rating"] = df["rating"].apply(lambda x: float(x) if x != "N/A" else 0.0)
    
    # Clean reviews: Convert to int
    df["reviews"] = df["reviews"].apply(lambda x: int(x.replace("(", "").replace(")", "")) if x != "0" else 0)
    
    # Handle missing brands
    df["brand"] = df["brand"].replace("N/A", "Unknown")
    
    # Ensure data types
    df["title"] = df["title"].astype(str)
    df["image_url"] = df["image_url"].astype(str)
    df["product_url"] = df["product_url"].astype(str)
    
    return df

def save_to_csv(df: pd.DataFrame, filename: str = None):
    """Save cleaned data to CSV with error handling."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_soft_toys_{timestamp}.csv"
    
    try:
        df.to_csv(filename, index=False, encoding="utf-8")
        logger.info(f"Raw data saved to {filename}")
    except PermissionError as e:
        logger.info(f"Permission denied when saving to {filename}: {e}")
        logger.info("Please close the file if it's open in another application, or try saving to a different filename.")
        new_filename = f"amazon_soft_toys_backup_{timestamp}.csv"
        logger.info(f"Attempting to save to {new_filename} instead...")
        df.to_csv(new_filename, index=False, encoding="utf-8")
        logger.info(f"Raw data saved to {new_filename}")

def save_analysis_to_excel(brand_data: Dict, price_data: Dict, review_data: Dict, filename: str = "analysis_results.xlsx"):
    """Save analysis results to an Excel file with multiple sheets."""
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        # Brand Performance Analysis
        top_5_brands_df = pd.DataFrame(brand_data["top_5_brands"]).reset_index()
        top_5_brands_df.columns = ["Brand", "Frequency"]
        top_5_brands_df.to_excel(writer, sheet_name="Brand Performance", index=False, startrow=0)
        
        avg_rating_df = pd.DataFrame(brand_data["avg_rating"]).reset_index()
        avg_rating_df.columns = ["Brand", "Avg Rating"]
        avg_rating_df["Avg Rating"] = avg_rating_df["Avg Rating"].round(2)
        startrow = len(top_5_brands_df) + 2
        avg_rating_df.to_excel(writer, sheet_name="Brand Performance", index=False, startrow=startrow)
        
        high_rated_df = pd.DataFrame({"High-Rated Less Frequent Brands": brand_data["high_rated_low_freq"]})
        startrow += len(avg_rating_df) + 2
        high_rated_df.to_excel(writer, sheet_name="Brand Performance", index=False, startrow=startrow)
        
        # Price vs. Rating Analysis
        avg_price_df = pd.DataFrame(price_data["avg_price"]).reset_index()
        avg_price_df.columns = ["Rating Range", "Avg Price (₹)"]
        avg_price_df["Avg Price (₹)"] = avg_price_df["Avg Price (₹)"].round(2)
        avg_price_df.to_excel(writer, sheet_name="Price vs Rating", index=False, startrow=0)
        
        high_value_df = price_data["high_value"][["title", "price", "rating"]].copy()
        high_value_df["price"] = high_value_df["price"].round(2)
        high_value_df["rating"] = high_value_df["rating"].round(2)
        startrow = len(avg_price_df) + 2
        high_value_df.to_excel(writer, sheet_name="Price vs Rating", index=False, startrow=startrow)
        
        overpriced_df = price_data["overpriced"][["title", "price", "rating"]].copy()
        overpriced_df["price"] = overpriced_df["price"].round(2)
        overpriced_df["rating"] = overpriced_df["rating"].round(2)
        startrow += len(high_value_df) + 2
        overpriced_df.to_excel(writer, sheet_name="Price vs Rating", index=False, startrow=startrow)
        
        # Review & Rating Distribution
        top_reviews_df = review_data["top_reviews"][["title", "reviews", "rating"]].copy()
        top_reviews_df["rating"] = top_reviews_df["rating"].round(2)
        top_reviews_df.to_excel(writer, sheet_name="Review & Rating", index=False, startrow=0)
        
        top_rated_df = review_data["top_rated"][["title", "rating", "reviews"]].copy()
        top_rated_df["rating"] = top_rated_df["rating"].round(2)
        startrow = len(top_reviews_df) + 2
        top_rated_df.to_excel(writer, sheet_name="Review & Rating", index=False, startrow=startrow)
        
        high_rated_low_reviews_df = review_data["high_rated_low_reviews"][["title", "rating", "reviews"]].copy()
        high_rated_low_reviews_df["rating"] = high_rated_low_reviews_df["rating"].round(2)
        startrow += len(top_rated_df) + 2
        high_rated_low_reviews_df.to_excel(writer, sheet_name="Review & Rating", index=False, startrow=startrow)
    
    logger.info(f"Analysis results saved to {filename}")

def brand_performance_analysis(df: pd.DataFrame) -> Dict:
    """Perform brand performance analysis."""
    # Brand frequency
    brand_freq = df["brand"].value_counts()
    top_5_brands = brand_freq.head(5)
    
    # Average rating by brand
    avg_rating_by_brand = df.groupby("brand")["rating"].mean().sort_values(ascending=False).head(5)
    
    # High-rated but less frequent brands
    high_rated_low_freq = avg_rating_by_brand[avg_rating_by_brand > 4.0].index
    high_rated_low_freq = [brand for brand in high_rated_low_freq if brand_freq.get(brand, 0) < 3]
    
    # Visualizations
    plt.figure(figsize=(10, 6))
    top_5_brands.plot(kind="bar", color="skyblue", edgecolor="black")
    plt.title("Top 5 Brands by Frequency", fontsize=14, pad=15)
    plt.xlabel("Brand", fontsize=12)
    plt.ylabel("Number of Products", fontsize=12)
    plt.xticks(rotation=45, fontsize=10)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("top_5_brands_frequency.png", dpi=300)
    plt.close()
    
    # plt.figure(figsize=(8, 8))
    # top_5_brands.plot(kind="pie", autopct="%1.1f%%", startangle=90, textprops={"fontsize": 12})
    # plt.title("Percentage Share of Top Brands", fontsize=14, pad=15)
    # plt.ylabel("")
    # plt.tight_layout()
    # plt.savefig("top_brands_share.png", dpi=300)
    # plt.close()
    
    return {
        "top_5_brands": top_5_brands,
        "avg_rating": avg_rating_by_brand,
        "high_rated_low_freq": high_rated_low_freq
    }

def price_vs_rating_analysis(df: pd.DataFrame) -> Dict:
    """Perform price vs. rating analysis."""
    df_filtered = df[(df["price"] > 0) & (df["rating"] > 0)].copy()
    
    bins = [0, 2, 3, 4, 5]
    labels = ["0-2", "2-3", "3-4", "4-5"]
    df_filtered.loc[:, "rating_range"] = pd.cut(df_filtered["rating"], bins=bins, labels=labels, include_lowest=True)
    avg_price_by_rating = df_filtered.groupby("rating_range", observed=True)["price"].mean().round(2)
    
    high_value = df_filtered[(df_filtered["rating"] >= 4.0) & (df_filtered["price"] <= df_filtered["price"].quantile(0.25))]
    overpriced = df_filtered[(df_filtered["rating"] <= 3.0) & (df_filtered["price"] >= df_filtered["price"].quantile(0.75))]
    
    plt.figure(figsize=(10, 6))
    plt.scatter(df_filtered["rating"], df_filtered["price"], alpha=0.5, color="teal", edgecolor="black")
    plt.title("Price vs. Rating", fontsize=14, pad=15)
    plt.xlabel("Rating", fontsize=12)
    plt.ylabel("Price (₹)", fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.7)
    for _, row in high_value.iterrows():
        plt.annotate("High Value", (row["rating"], row["price"]), fontsize=10, color="red")
    plt.tight_layout()
    plt.savefig("price_vs_rating_scatter.png", dpi=300)
    plt.close()
    
    plt.figure(figsize=(10, 6))
    avg_price_by_rating.plot(kind="bar", color="lightgreen", edgecolor="black")
    plt.title("Average Price by Rating Range", fontsize=14, pad=15)
    plt.xlabel("Rating Range", fontsize=12)
    plt.ylabel("Average Price (₹)", fontsize=12)
    plt.xticks(rotation=0, fontsize=10)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("avg_price_by_rating_range.png", dpi=300)
    plt.close()
    
    return {
        "avg_price": avg_price_by_rating,
        "high_value": high_value,
        "overpriced": overpriced
    }

def review_rating_distribution(df: pd.DataFrame) -> Dict:
    """Analyze review and rating distribution."""
    top_reviews = df.nlargest(5, "reviews")[["title", "reviews", "rating"]]
    top_rated = df[df["rating"] > 0].nlargest(5, "rating")[["title", "rating", "reviews"]]
    high_rated_low_reviews = df[(df["rating"] >= 4.5) & (df["reviews"] <= df["reviews"].quantile(0.25))][["title", "rating", "reviews"]]
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="reviews", y="title", hue="title", data=top_reviews, palette="Blues_d", legend=False)
    plt.title("Top 5 Products by Number of Reviews", fontsize=14, pad=15)
    plt.xlabel("Number of Reviews", fontsize=12)
    plt.ylabel("Product Title", fontsize=12)
    plt.grid(True, axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("top_5_reviews.png", dpi=300)
    plt.close()
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x="rating", y="title", hue="title", data=top_rated, palette="Greens_d", legend=False)
    plt.title("Top 5 Products by Rating", fontsize=14, pad=15)
    plt.xlabel("Rating", fontsize=12)
    plt.ylabel("Product Title", fontsize=12)
    plt.grid(True, axis="x", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("top_5_ratings.png", dpi=300)
    plt.close()
    
    return {
        "top_reviews": top_reviews,
        "top_rated": top_rated,
        "high_rated_low_reviews": high_rated_low_reviews
    }

def main():
    """Main function to scrape, clean, and analyze Amazon soft toys data."""
    try:
        products = scrape_amazon_products(max_products=20, max_pages=3)
        
        if not products:
            logger.info("No eligible products found.")
            return
        
        # Clean and prepare data
        df = clean_data(products)
        save_to_csv(df)
        
        # Perform analyses and save to Excel
        brand_data = brand_performance_analysis(df)
        price_data = price_vs_rating_analysis(df)
        review_data = review_rating_distribution(df)
        save_analysis_to_excel(brand_data, price_data, review_data)
        
        logger.info("Analysis complete. Visualizations saved as PNG files.")
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user.")
    except Exception as e:
        logger.info(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()