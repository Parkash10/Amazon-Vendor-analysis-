import sqlite3
import logging 
import time
import pandas as pd

# Setup logging
logging.basicConfig(filename="logs/final_task.log", 
                    level=logging.DEBUG, 
                    format="%(asctime)s - %(levelname)s - %(message)s",
                    filemode="a")

def final_summary(conn):
    """ This function merges different tables to get a final summary and add new important columns."""
    final_table = pd.read_sql_query("""
        WITH FreightSummary AS (
            SELECT 
                VendorNumber, 
                SUM(Freight) AS FreightCost 
            FROM vendor_invoice 
            GROUP BY VendorNumber
        ),
        PurchaseSummary AS (
            SELECT
                p.VendorNumber,
                p.VendorName,
                p.Brand,
                p.Description,
                p.PurchasePrice,
                pp.Volume,
                pp.Price AS ActualPrice,
                SUM(p.Quantity) AS TotalPurchaseQuantity,
                SUM(p.Dollars) AS TotalPurchaseDollars
            FROM Purchases p 
            JOIN Purchase_Prices pp ON p.Brand = pp.Brand
            WHERE p.PurchasePrice > 0
            GROUP BY p.VendorNumber, p.VendorName, p.Brand, p.Description, p.PurchasePrice, pp.Volume, pp.Price
        ), 
        SalesSummary AS (
            SELECT 
                VendorNo,
                Brand,
                SUM(SalesDollars) AS TotalSaleDollars,
                SUM(SalesPrice) AS TotalSalePrice,
                SUM(SalesQuantity) AS TotalSaleQuantity,
                SUM(ExciseTax) AS TotalExciseTax
            FROM sales 
            GROUP BY VendorNo, Brand
        )

        SELECT 
            ps.VendorNumber,
            ps.VendorName,
            ps.Brand,
            ps.Description, 
            ps.PurchasePrice,
            ps.ActualPrice,
            ps.Volume,
            ps.TotalPurchaseQuantity,
            ps.TotalPurchaseDollars,
            ss.TotalSaleQuantity,
            ss.TotalSaleDollars,
            ss.TotalSalePrice,
            ss.TotalExciseTax,
            COALESCE(fs.FreightCost, 0) AS FreightCost
        FROM PurchaseSummary ps 
        LEFT JOIN SalesSummary ss ON ps.VendorNumber = ss.VendorNo AND ps.Brand = ss.Brand
        LEFT JOIN FreightSummary fs ON ps.VendorNumber = fs.VendorNumber
        ORDER BY ps.TotalPurchaseDollars DESC
    """, conn)
    
    return final_table

def clean_data(df):
    """Clean and enrich the data with calculated fields."""

    df["Volume"] = df["Volume"].astype(float)
    df.fillna(0, inplace=True)

    df["VendorNumber"] = df["VendorNumber"].astype(str).str.strip()
    df["Description"] = df["Description"].astype(str).str.strip()

    df["GrossProfit"] = df["TotalSaleDollars"] - df["TotalPurchaseDollars"]
    df["MarginProfit"] = (df["GrossProfit"] / df["TotalSaleDollars"]).replace([float('inf'), -float('inf')], 0) * 100
    df["StockTurnover"] = df["TotalSaleQuantity"] / df["TotalPurchaseQuantity"].replace(0, 1)
    df["TotalSaleToPurchaseRatio"] = df["TotalSaleDollars"] / df["TotalPurchaseDollars"].replace(0, 1)

    return df

def ingest_db(df, table_name, conn):
    """ Ingest DataFrame into SQLite database."""
    df.to_sql(table_name, conn, if_exists="replace", index=False)

if __name__ == "__main__":
    try:
        conn = sqlite3.connect("inventory.db")
        
        logging.info("Creating vendor summary table...")
        summary_df = final_summary(conn)
        logging.info("Initial Summary Loaded Successfully")

        logging.info("Cleaning the data ...")
        clean_df = clean_data(summary_df)
        logging.info("Data Cleaned Successfully")

        logging.info("Ingesting the data to final_table ...")
        ingest_db(clean_df, "final_table", conn)
        logging.info("Final data ingested successfully")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

     