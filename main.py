import pandas as pd
from datetime import datetime
import streamlit as st
import pdfplumber
import re
from typing import BinaryIO


def parse_single_page_pdf(file: BinaryIO) -> list[dict]:

    # Attempt to extract text from the first page of the PDF
    try:
        with pdfplumber.open(file) as pdf:
            if not pdf.pages:
                raise ValueError("The PDF has no pages.")
            page = pdf.pages[0]
            text = page.extract_text()
            if not text:
                raise ValueError("No text could be extracted from the PDF.")
    except Exception as e:
        raise RuntimeError(f"Error reading PDF: {e}")

    # Define the range of interest within the extracted text
    start = text.find("COLLECTED DISTRIBUTED")
    end = text.find("ENTITY")

    if start == -1 or end == -1 or start >= end:
        raise ValueError(
            "Could not locate valid 'COLLECTED DISTRIBUTED' and 'ENTITY' section in the text."
        )

    # find the start date and end date
    date__text_block_start = text.find("FROM")
    date__text_block_end = text.find("YEAR FROM")

    if date__text_block_start == -1 or date__text_block_end == -1:
        raise ValueError(
            "Could not locate valid START_DATE and END_DATE section in the text."
        )

    # Clean the text: Remove all characters except digits (0-9), slashes (/), and spaces
    # This preserves typical date formats like "06/01/2025" and separates multiple dates with a space
    date_text = text[date__text_block_start:date__text_block_end]
    date_text = re.sub(r"[^0-9/ ]", "", date_text)
    dates = list(filter(None, date_text.split(" ")))

    # Defensive check to avoid IndexError in case there aren't two dates
    if len(dates) < 2:
        raise ValueError("Expected two dates in the text block, but found fewer.")

    # Assign the start and end dates
    start_date = datetime.strptime(dates[0], "%m/%d/%Y")
    end_date = datetime.strptime(dates[0], "%m/%d/%Y")

    # Clean and filter the extracted section
    section = text[start:end]
    section = section.replace("-", "")  # Remove dashes
    section = section.replace("%", "")  # Remove percent symbols
    lines = section.strip().split("\n")
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "COLLECTED DISTRIBUTED" in line or "TOTL" in line:
            continue
        cleaned_line = re.sub(r"\s+", " ", line)  # Replace multiple spaces with one
        cleaned_lines.append(cleaned_line)

    # Parse the cleaned lines into structured rows
    rows = []
    for i, line in enumerate(cleaned_lines):
        split = line.split(" ")
        if len(split) < 13:
            raise ValueError(f"Line {i+1} has fewer than 13 expected values: {line}")
        try:
            row = {
                "start_date": start_date,
                "end_date": end_date,
                "year": int(split[0]),
                "beginning_tax_balance": float(split[1]),
                "tax_adjustment": float(split[2]),
                "base_tax_collected": float(split[3]),
                "reversals": float(split[4]),
                "net_base_tax_collected": float(split[5]),
                "percent_collected": float(split[6]),
                "ending_tax_balance": float(split[7]),
                "property_and_insurance_collected": float(split[8]),
                "property_and_insurance_reversals": float(split[9]),
                "local_real_property_collected": float(split[10]),
                "other_penalty_collected": float(split[11]),
                "total_distributed": float(split[12]),
            }
        except ValueError as ve:
            raise ValueError(
                f"Failed to convert values to numbers in line {i+1}: {line}\nError: {ve}"
            )
        rows.append(row)

    # Write the structured data to a CSV file
    if not rows:
        raise ValueError("No valid data rows to write to CSV.")

    return rows


rows = parse_single_page_pdf("test_data\\2025.01.24 - 01.26   12748338.55.pdf")
rows
