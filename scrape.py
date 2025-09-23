import requests
from bs4 import BeautifulSoup

def scrape_quotes():
    url = "http://quotes.toscrape.com/"   # Example site
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all quote blocks
        quotes = soup.find_all("span", class_="text")
        authors = soup.find_all("small", class_="author")

        for i in range(len(quotes)):
            print(f"Quote: {quotes[i].get_text()}")
            print(f"Author: {authors[i].get_text()}")
            print("-" * 40)
    else:
        print("Failed to retrieve page")

if __name__ == "__main__":
    scrape_quotes()
