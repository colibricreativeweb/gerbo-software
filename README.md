# Gerbo Software &middot; ![Release Status](https://img.shields.io/badge/release-v2.2.0-green) [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Are you tired of manual data mining tasks? Look no further! Our project provides a robust solution for extracting email addresses and phone numbers using Google’s Custom Search API and Python’s HTMLParser, also it includes document scraping capabilities. Whether you’re a penetration tester or a curious learner, this educational app is designed to help you explore data mining techniques.

## :gear: Install & Run

Just fire up `gerbo-gui.py` to use the fully-featured GUI on your favorite browser.

```bash
python gerbo-gui.py
```

## :key: Environment Variables

This application requires two environment variables: `GOOGLE_API_KEY` and `GOOGLE_CX_KEY`. These are used to authenticate with Google's Custom Search JSON API.

You can set these variables in a `.env` file in the root of the project. Here's an example:

```plaintext
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CX_KEY=your_google_cx_key
```

Replace `your_google_api_key` and `your_google_cx_key` with your actual keys.

To get these keys, you need to create a Custom Search JSON API and a Programmable Search Engine in your Google Cloud Console. Detailed instructions can be found in the [Custom Search JSON API documentation](https://developers.google.com/custom-search/v1/overview).

## :shipit: Disclaimer

This application is intended solely for educational purposes. We do not endorse or encourage any illegal or unethical use of the extracted information. Use it responsibly and respect privacy laws.

## :star2: Main features

- **Simple:** It just works.
- **Awesome:** Like you, you're awesome.
- **Google API Integration:** Leverages Google's powerful search API for accurate results.
- **Customizable Search:** Allows optional country and language selection for more targeted searching.
- **Exclusion of Words:** Allows users to exclude specific words from the search.
- **Selective Search:** Allows users to select specific columns to search.
- **Multi-file Support:** Can process multiple Excel files at once.
- **Unique Column Handling:** Handles duplicate column names across multiple files intelligently.
- **Manual Website Scraping:** Provides the ability to manually scrape websites for information.
- **PDF Scraping:** Extracts email addresses from PDF files.
- **Session Management:** Remembers your column selection across multiple searches.
- **Secure:** Uses secure file handling practices to keep your data safe.
- **Custom Database Naming:** Allows users to provide a custom name for the generated database.
- **Automated Database Creation:** Automatically creates a SQLite database from the search results.

## :world_map: Roadmap

Here are some features we're considering for future releases:

- [ ] **Database Viewing:** A built-in viewer to explore the generated SQLite database right from the application.
- [ ] **Database Search:** A search feature that allows users to search for specific data within the generated database.
- [ ] **Table Filtering:** The ability to filter the data in the generated database by specific criteria.
- [ ] **Walkthrough:** An interactive guide to help new users understand how to use the application.
- [ ] **User Authentication:** Secure user accounts, allowing users to save their search history and preferences.
- [ ] **API Integration:** The ability to send search results to an external API or receive data from other APIs.
- [ ] **Data Visualization:** Graphs and charts to visualize the search results and database data.
- [ ] **Export Options:** More options for exporting the search results, such as CSV, JSON, or direct export to a remote database.

## :scroll: Licensing

This work is licensed under a [MIT License](LICENSE).

## :brain: Acknowledgments

_"Whoever loves discipline loves knowledge, but whoever hates correction is stupid."_
