# Tech Hub Kenya — September Sales Analytics Pipeline

An automated, minimalist data analytics and integrity verification pipeline built for **Tech Hub Kenya** (Nairobi, Kenya) to ingest, clean, and profile retail transaction data across five regional shop locations.

## 🚀 Execution Instructions

Follow these step-by-step setup commands inside your terminal window to initialize your environment and execute the pipeline:

### 1. Configure the Virtual Workspace Environment
Isolate your package manager dependencies cleanly from your global system environment variables:
```bash

source venv/Scripts/activate
```

### 2. Install Development Tooling Assets
Update your local isolated venv layer with necessary validation framework libraries:
```bash
pip install -r requirements.txt
```

### 3. Run the Sales Core Pipeline Engine
Execute the central script loop directly using your terminal shell interpreter prompt line:
```bash
python sales_analysis.py
```
Upon execution, the pipeline dynamically loads the dirty file registry from `data/electronics_sales.csv`, handles row validations, saves a detailed business document to `output/sales_report.txt`, and runs cross-examination tests against a local Pandas array wrapper.

---

## Data Cleaning Protocols & Justifications

The til system export dataset features a series of unstructured, hand-typed values. The pipeline implements explicit parsing rules inside `convert_rows()` to ensure calculation safety:

* **Text-to-Numeric Sifting:** Text strings containing localized padding layout properties (like `"KES "` or formatted thousands-separation commas) are dynamically stripped and converted to native floats. 
* **Missing & Empty Records Exclusion:** Any row lacking a trackable element inside either the `quantity` or `unit_price` columns is dropped from the operational queue. Without these values, evaluating a transaction's revenue baseline is mathematically impossible.
* **Non-Positive Quantity Filtering (`quantity <= 0`):** Transactions registering a unit count of zero or a negative value are flagged as invalid registry metrics and isolated from calculation totals.
* **Negative Price Boundary Interception (`unit_price < 0`):** Hand-typed inputs indicating a negative balance number are dropped to preserve ledger integrity and prevent false revenue calculation deductions.

*All isolated or dropped entries are compiled sequentially inside a distinct trackable list payload called `skipped_rows` containing direct descriptive string reasons.*

---

## Implementation & Sorting Logic

* **Pure Python Standard Library Constraints:** All major business calculations, multi-field groupings (by product, shop branch, and payment strategy), list comprehension filters, and statistical reductions (Tasks 1 through 7) are engineered from scratch without relying on external packages, `defaultdict`, or the `Counter` module helper shortcuts.
* **Task 5 Tie-Breaker Ranking Resolution:** To ensure stable product leaderboard evaluations, ties are resolved systematically using a secondary structural string weight factor: `key=lambda item: (-item[1], item[0])`. This forces the system to sort descending by raw revenue performance first, and then break any identical cash match by alphabetizing the product string names ascending.
* **Task 7 Manual Analytics Aggregations:** Custom algorithmic loops calculate arithmetic `mean`, middle-element `median`, and range-boundary limits (`minimum_maximum`) entirely manually—omitting native built-ins like `min()` or `max()`. Clean validation guards assert a clear `ValueError` exception state if an empty data stream is passed to prevent division-by-zero crashes.

---

## Operational Assertions & Verification System

Task 8 executes a diagnostic test loop comparing native loop data metrics directly against an isolated `pandas.DataFrame` processing matrix. 

To bypass tiny floating-point arithmetic deviations introduced by machine-level binary code storage boundaries, threshold checks are stabilized using an absolute distance margin: `abs(pandas_result - python_result) < 0.01`. A perfect **`MATCH`** status is logged to the system console only if the calculations match to within 1 cent.

Built by [Jesse Ngugi](https://ngugi.pages.dev)