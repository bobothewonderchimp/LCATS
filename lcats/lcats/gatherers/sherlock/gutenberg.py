"""Corpus extractor for the Sherlock Holmes stories."""

from bs4 import BeautifulSoup

import lcats.gatherers.downloaders as downloaders


ADVENTURES_GUTENBERG = 'https://www.gutenberg.org/files/1661/1661-h/1661-h.htm'
ADVENURES_SCANDAL_HEADING = "A SCANDAL IN BOHEMIA"


def find_paragraphs_adventures(soup, start_heading_text):
    """Find paragraphs following a specific heading in a BeautifulSoup object."""
    # Find the start heading - this is brittle and may need to be adjusted for different stories.
    start_heading = soup.find(
        lambda tag: tag.name in ('h2', 'h3') and start_heading_text in tag.get_text(strip=True))

    if start_heading is None:
        return None
    
    # If we got the heading, try to return the paragraphs following it
    paragraphs = []
    current_element = start_heading.find_next_sibling()

    # Iterate through sibling elements until the next heading or the end of the siblings is reached.
    while current_element and current_element.name not in ('h2', 'div'):
        if current_element.name == 'p':
            paragraphs.append(current_element.get_text(strip=False))
        current_element = current_element.find_next_sibling()

    return '\n'.join(paragraphs)


def create_download_callback(story_name, url, start_heading_text, description):
    """Create a download callback function for a specific story."""
    def story_download_callback():
        """Download a specific Sherlock story from the Gutenberg Project."""
        story_gutenberg = downloaders.load_page(url)
        story_soup = BeautifulSoup(story_gutenberg, "lxml")

        story_text = find_paragraphs_adventures(story_soup, start_heading_text)
        story_data = {
            "author": "Arthur Conan Doyle",
            "year": 1891,
            "url": url,
            "name": story_name,
        }

        return description, story_text, story_data

    return story_name, story_download_callback


def gather():
    """Run DataGatherers for the Sherlock Holmes corpus."""
    gatherer = downloaders.DataGatherer(
        "sherlock", description="Sherlock Holmes stories from the Gutenberg Project.")
    gatherer.download(
        *create_download_callback("scandal_in_bohemia", 
                                  ADVENTURES_GUTENBERG, 
                                  ADVENURES_SCANDAL_HEADING,
                                  "Sherlock Holmes - A Scandal in Bohemia"))
    return gatherer.downloads


def main():
    """Extract the Sherlock Holmes stories from the Gutenberg Project."""
    print("Gathering Sherlock Holmes stories.")
    downloads = gather()
    print(f" - Total stories in Sherlock corpus: {len(downloads)}")


if __name__ == "__main__":
    main()