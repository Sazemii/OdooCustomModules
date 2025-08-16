# MSC Invoice Report Module

This module customizes the Odoo sales invoice report with the following changes:

## Features

1. **Removes Company Logo**: The company logo is removed from the invoice header
2. **Large Company Name**: Company name is displayed prominently in large font (2.5rem)
3. **Branch VAT/TIN**: Displays branch-specific VAT/TIN below the company name with "VAT Reg. TIN:" label
4. **Branch Address**: Shows the complete branch address in a single line below the VAT/TIN
5. **Smaller Font**: VAT/TIN and address use smaller font size (0.9rem) compared to company name

## Installation

1. Copy the `msc_invoice` folder to your Odoo `custom_addons` directory
2. Restart your Odoo server
3. Go to Apps menu and update the apps list
4. Search for "MSC Invoice Report" and install it

## Configuration

After installation:

1. Go to Settings > Companies > Companies
2. Edit your company record
3. Fill in the "Branch VAT/TIN" field with your branch-specific VAT or TIN number
4. Ensure your company address fields are properly filled

## Usage

The customized invoice report will automatically be used for all sales invoices. The changes include:

- Company name displayed prominently at the top
- Branch VAT/TIN displayed below the company name
- Complete branch address in one line
- Professional formatting with appropriate font sizes

## File Structure

```
msc_invoice/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── account_move.py
├── views/
│   ├── company_view.xml
│   └── report_invoice.xml
└── security/
    └── ir.model.access.csv
```

## Technical Details

- Inherits from `account.report_invoice_document` template
- Adds `branch_vat_tin` field to `res.company` model
- Creates custom external layout template
- Uses conditional rendering to avoid empty fields
- Maintains compatibility with existing invoice functionality
