import csv
from pathlib import Path
import pandas as pd

DATA_PATH = Path("data") / "electronics_sales.csv"


def read_sales(path: Path = DATA_PATH) -> list[dict[str, str]]:
    """Read the CSV with the csv module and return the raw rows."""
    raw_rows = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print(f"Column names found: {reader.fieldnames}")
        for row in reader:
            raw_rows.append(row)
    print(f"Total rows scanned: {len(raw_rows)}\n")
    return raw_rows

def parse_number(value: str) -> float | None:
    """Convert a messy numeric string to a float, or return None if it cannot be trusted."""
    if not value or str(value).strip() == "":
        return None
    try:
        # Remove any currency symbols or commas
        cleaned_value = value.replace("$", "").replace(",", "").strip()
        return float(cleaned_value)
    except ValueError:
        return None

def convert_rows(rows: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    """Return (clean_rows, skipped_rows). Clean rows have numeric quantity, unit price and revenue."""
    clean_rows = []
    skipped_rows = []

    for idx, r in enumerate(rows, start=1):
        raw_qty = r.get("quantity", "")
        raw_price = r.get("unit_price", "")

        parsed_qty = parse_number(raw_qty)
        parsed_price = parse_number(raw_price)

        # Validation checks to intercept un-reparable strings or anomalies
        if parsed_qty is None:
            skipped_rows.append({"row_index": idx, "data": r, "reason": f"Invalid/missing quantity string: '{raw_qty}'"})
            continue
        if parsed_price is None:
            skipped_rows.append({"row_index": idx, "data": r, "reason": f"Invalid/missing unit price string: '{raw_price}'"})
            continue
        if parsed_qty <= 0:
            skipped_rows.append({"row_index": idx, "data": r, "reason": f"Non-positive quantity boundary detected: {parsed_qty}"})
            continue
        if parsed_price < 0:
            skipped_rows.append({"row_index": idx, "data": r, "reason": f"Negative pricing boundary configuration: {parsed_price}"})
            continue
            
        # Build the compliant dictionary adding explicit clean data metrics
        clean_record = dict(r)
        clean_record["quantity"] = int(parsed_qty)  # Whole integers
        clean_record["unit_price"] = parsed_price
        
        # Calculate the derived revenue dimension to satisfy task criteria
        clean_record["revenue"] = clean_record["quantity"] * clean_record["unit_price"]
        
        clean_rows.append(clean_record)
        
    return clean_rows, skipped_rows


def total_revenue(rows: list[dict]) -> float:
    """Total revenue across all clean rows."""
    total = 0.0
    for row in rows:
        #pull from our clean row
        total += row.get("revenue", 0.0)
    return total


def revenue_by(rows: list[dict], field: str) -> dict[str, float]:
    """Total revenue grouped by any column (product, store, payment_method...)."""
    grouped_totals = {}

    for row in rows:
        # Get the group name (e.g "Nairobi") safely
        group_key = row.get(field)
        if not group_key:
            continue

        row_revenue = row.get("revenue", 0.0)

        if group_key in grouped_totals:
            grouped_totals[group_key] += row_revenue
        else:
            grouped_totals[group_key] = row_revenue
    
    return grouped_totals


def top_n(totals: dict[str, float], n: int = 3) -> list[tuple[str, float]]:
    """Return the n highest (key, value) pairs, highest first."""
    sorted_items = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return sorted_items[:n]


def high_value(rows: list[dict], threshold: float) -> list[dict]:
    """Transactions whose revenue is at or above threshold (use a comprehension)."""
    return [row for row in rows if row.get("revenue", 0.0) >= threshold]


# Reusable statistics - implement these yourself, no statistics module.
def mean(values: list[float]) -> float:
    #Calculating the arithmetic mean of a list of values
    if not values:
        raise ValueError("Cannot calculate mean from an empty list of values.")
    total_sum = 0.0
    for value in values:
        total_sum += value
    return total_sum / len(values)


def median(values: list[float]) -> float:
    if not values:
        raise ValueError("Cannot calculate median from an empty list of values.")
    sorted_values = sorted(values)
    n = len(sorted_values)
    midpoint = n // 2

    # For an odd count, pick the middle value; for an even count, average the two middle values
    if n % 2 != 0:
        return sorted_values[midpoint]
    else:
        return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def minimum_maximum(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("Cannot calculate minimum and maximum from an empty list of values.")

    current_min = values[0]
    current_max = values[0]
    for value in values:
        if value < current_min:
            current_min = value
        if value > current_max:
            current_max = value
    
    return current_min, current_max


def verify_with_pandas(path: Path, my_results: dict) -> None:
    """Recompute the headline numbers with pandas and print whether each one matches."""
    print("==================================================")
    print("        PANDAS VERIFICATION CHECKS                ")
    print("==================================================\n")
    
    try:
        # Load the dirty data asset directly into a DataFrame matrix
        df = pd.read_csv(path)
        
        # Re-apply our custom data cleaning
        for col in ['quantity', 'unit_price']:
            df[col] = df[col].astype(str).str.replace('KES', '', case=False)
            df[col] = df[col].str.replace(',', '').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # Drop rows missing critical numeric entries
        df = df.dropna(subset=['quantity', 'unit_price'])
        df = df[(df['quantity'] > 0) & (df['unit_price'] >= 0)]
        
        # Force correct whole data types and compute the derived metrics
        df['quantity'] = df['quantity'].astype(int)
        df['revenue'] = df['quantity'] * df['unit_price']
        
        # 1. Verify Grand Total Revenue
        pd_total_rev = float(df['revenue'].sum())
        match_total = "MATCH" if abs(pd_total_rev - my_results['total_revenue']) < 0.01 else "MISMATCH"
        print(f"Grand Total Revenue Validation : {match_total} (Manual Python: {my_results['total_revenue']:.2f} | Pandas: {pd_total_rev:.2f})")
        
        # 2. Verify Revenue Metrics Means
        pd_mean = float(df['revenue'].mean())
        match_mean = "MATCH" if abs(pd_mean - my_results['mean_revenue']) < 0.01 else "MISMATCH"
        print(f"Transaction Mean Validation    : {match_mean} (Manual Python: {my_results['mean_revenue']:.2f} | Pandas: {pd_mean:.2f})")
        
        # 3. Verify Revenue Midpoint Midpoint
        pd_median = float(df['revenue'].median())
        match_median = "MATCH" if abs(pd_median - my_results['median_revenue']) < 0.01 else "MISMATCH"
        print(f"Transaction Median Validation  : {match_median} (Manual Python: {my_results['median_revenue']:.2f} | Pandas: {pd_median:.2f})")
        
    except Exception as e:
        print(f"Pandas cross-check validation failed to complete: {e}")


if __name__ == "__main__":
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    report_file_path = output_dir / "sales_report.txt"
    
    print("==================================================")
    print("     TECH HUB KENYA - SEPTEMBER SALES PIPELINE    ")
    print("==================================================\n")
    
    # 1. Ingest Data Asset
    raw_dataset = read_sales(DATA_PATH)
    if not raw_dataset:
        print("[TERMINATED] Direct file parsing returned empty records.")
        exit(1)
        
    # 2. Restructure and Clean Input Vectors
    clean_transactions, dropped_ledger = convert_rows(raw_dataset)
    print(f"[CLEAN COMPLETE] Valid Transactions: {len(clean_transactions)} | Skipped Rows: {len(dropped_ledger)}")
    
    # 3. Execute Primary Mathematical Reductions
    grand_revenue = total_revenue(clean_transactions)
    
    # 4. Group Aggregations
    by_product_revenue = revenue_by(clean_transactions, "product")
    by_store_revenue = revenue_by(clean_transactions, "store")
    by_payment_revenue = revenue_by(clean_transactions, "payment_method")
    
    # 5. Calculate Rankings Order Matrix
    top_three_products = top_n(by_product_revenue, n=3)
    
    # 6. Filter High Value Target Windows
    premium_sales_threshold = 50000.0
    qualifying_deals = high_value(clean_transactions, premium_sales_threshold)
    
    # Store-by-store high value volume count via a required dictionary comprehension tracking loop
    unique_stores = {row['store'] for row in clean_transactions if row.get('store')}
    high_value_store_counts = {
        store: len([r for r in qualifying_deals if r.get('store') == store]) 
        for store in unique_stores
    }
    
    # 7. Extract Custom Statistical Arrays
    transaction_revenue_stream = [row['revenue'] for row in clean_transactions]
    avg_deal_size = mean(transaction_revenue_stream)
    midpoint_deal_size = median(transaction_revenue_stream)
    floor_deal, ceiling_deal = minimum_maximum(transaction_revenue_stream)
    
    # Compile the results container to feed straight into Task 8 verification checks
    headline_metrics_results = {
        "total_revenue": grand_revenue,
        "mean_revenue": avg_deal_size,
        "median_revenue": midpoint_deal_size
    }
    
    # =====================================================================
    # GENERATING A PRINTED SALES REPORT TEXT FILE (output/sales_report.txt)
    # =====================================================================
    report_buffer = []
    report_buffer.append("==================================================")
    report_buffer.append("         TECH HUB KENYA - SEPTEMBER REVENUES      ")
    report_buffer.append("==================================================")
    report_buffer.append(f"Grand Total Revenue            : KES {grand_revenue:,.2f}")
    report_buffer.append(f"Total Operational Clean Rows   : {len(clean_transactions)}")
    report_buffer.append(f"Total Rows Excluded/Dropped    : {len(dropped_ledger)}\n")
    
    report_buffer.append("--- Revenue Distribution Ranking By Product ---")
    # Loop over product aggregation to list descending metrics
    sorted_all_products = sorted(by_product_revenue.items(), key=lambda x: (-x[1], x[0]))
    for prod, rev in sorted_all_products:
        report_buffer.append(f" * {prod:<25}: KES {rev:,.2f}")
        
    report_buffer.append("\n--- Top Three Products Leaderboard ---")
    for rank, (prod, rev) in enumerate(top_three_products, start=1):
        report_buffer.append(f" {rank}. {prod:<26}: KES {rev:,.2f}")
        
    report_buffer.append(f"\n--- Follow-up High-Value Deals Tracker (>= KES {premium_sales_threshold:,.2f}) ---")
    report_buffer.append(f"Total High Value Deals Found   : {len(qualifying_deals)}")
    for deal in qualifying_deals:
        report_buffer.append(f" * Order #{deal.get('id','?')} | {deal.get('store'):<10} | {deal.get('product'):<15} | Qty: {deal.get('quantity')} | Total: KES {deal.get('revenue'):,.2f}")
        
    report_buffer.append("\n--- High-Value Volume Breakdown By Regional Location Shop ---")
    for store, count in sorted(high_value_store_counts.items(), key=lambda x: -x[1]):
        report_buffer.append(f" * {store:<15}: {count} premium sales transactions tracked")
        
    report_buffer.append("\n--- Operational Transaction Statistics Summary ---")
    report_buffer.append(f" Mean Transaction Revenue      : KES {avg_deal_size:,.2f}")
    report_buffer.append(f" Median Transaction Revenue    : KES {midpoint_deal_size:,.2f}")
    report_buffer.append(f" Minimum Single Order Size     : KES {floor_deal:,.2f}")
    report_buffer.append(f" Maximum Single Order Size     : KES {ceiling_deal:,.2f}")
    report_buffer.append("==================================================")
    
    # Writing the formatted payload buffer down to the physical report target destination asset
    with open(report_file_path, mode='w', encoding='utf-8') as report_out:
        report_out.write("\n".join(report_buffer) + "\n")
        
    print(f"[REPORT COMPILED] Saved structural logs data asset to: {report_file_path}\n")
    
    # 8. Pandas Automated Cross-Checks Verification
    verify_with_pandas(DATA_PATH, headline_metrics_results)
