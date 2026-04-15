# ESG Data Collector

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

A Streamlit app for collecting and scoring ESG data across suppliers and project sites — with GRI framework alignment, evidence upload, and automated scoring.

---

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/achmadnaufal/esg-data-collector.git
   cd esg-data-collector
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the app:
   ```bash
   streamlit run app.py
   ```

---

## Features

- Collect ESG metrics across Environmental, Social, and Governance dimensions
- GRI (Global Reporting Initiative) framework alignment for standardized disclosures
- Evidence file upload per metric with persistent storage
- Automated ESG scoring with visual dashboards
- Supplier and project site management
- Exportable reports in CSV format
- Audit trail for data submissions

---

## Sample Output

![Dashboard Screenshot](docs/screenshot.png)

> If the screenshot is not available, run locally with `streamlit run app.py` to see the app in action.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend / UI | Streamlit |
| Data Processing | Pandas |
| Visualizations | Plotly |
| Database | SQLite (via esg_data.db) |
| Testing | Pytest + pytest-cov |
| Language | Python 3.9+ |

---

## Project Structure

```
esg-data-collector/
├── app.py                  # Main Streamlit entry point
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT license
├── README.md               # Project documentation
├── .gitignore              # Git ignore rules
├── .streamlit/
│   └── config.toml         # Streamlit theme and server config
├── src/
│   ├── collectors/         # ESG data collection modules
│   ├── scorers/            # Automated scoring logic
│   ├── models/             # Data models and schemas
│   └── utils/              # Shared utilities
├── docs/
│   └── SCREENSHOTS.md      # App screenshots reference
├── demo/                   # Demo data and examples
└── tests/                  # Unit and integration tests
```

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
