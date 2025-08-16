# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    branch_vat_tin = fields.Char(string='Branch VAT/TIN', help='Branch specific VAT or TIN number')


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    is_cash_sales = fields.Boolean(
        string='Cash Sales',
        default=False,
        help='Check if this is a cash sales transaction'
    )
    
    is_charge_sales = fields.Boolean(
        string='Charge Sales', 
        default=False,
        help='Check if this is a charge sales transaction'
    )
    
    sc_pwd_nac_mov_solo_parent_id_no = fields.Integer(
        string='SC/PWD/NAC/MOV/SOLO Parent ID No:',
        help='Parent ID number for discount eligibility',
        tracking=True
    )
    
    discount_id_signature = fields.Binary(
        string='Discount ID Signature',
        attachment=True,
        help='Signature for discount ID verification'
    )
    
    @api.onchange('invoice_payment_term_id')
    def _onchange_payment_term_sales_type(self):
        """Auto-set sales type based on payment terms"""
        if self.invoice_payment_term_id:
            if self.invoice_payment_term_id.name == 'Immediate Payment':
                self.is_cash_sales = True
                self.is_charge_sales = False
            else:
                self.is_cash_sales = False
                self.is_charge_sales = True
        else:
            self.is_cash_sales = True
            self.is_charge_sales = False
    
    @api.onchange('is_cash_sales')
    def _onchange_cash_sales(self):
        """Ensure only one sales type is selected"""
        if self.is_cash_sales:
            self.is_charge_sales = False
    
    @api.onchange('is_charge_sales') 
    def _onchange_charge_sales(self):
        """Ensure only one sales type is selected"""
        if self.is_charge_sales:
            self.is_cash_sales = False
            
    @api.onchange('sc_pwd_nac_mov_solo_parent_id_no')
    def _onchange_sc_pwd_id(self):
        """Apply 5% ID Discount tax when SC/PWD/NAC/MOV/SOLO ID is provided"""
        if self.sc_pwd_nac_mov_solo_parent_id_no and self.invoice_line_ids:
            # Find the 5% ID Discount tax
            discount_tax = self.env['account.tax'].search([
                ('name', 'ilike', '5% ID Discount'),
                ('type_tax_use', '=', 'sale'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if discount_tax:
                for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                    # Only add the tax if it's not already applied
                    if discount_tax.id not in line.tax_ids.ids:
                        line.tax_ids = [(4, discount_tax.id, 0)]
        elif not self.sc_pwd_nac_mov_solo_parent_id_no and self.invoice_line_ids:
            # Remove the 5% ID Discount tax if ID is removed
            discount_tax = self.env['account.tax'].search([
                ('name', 'ilike', '5% ID Discount'),
                ('type_tax_use', '=', 'sale'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if discount_tax:
                for line in self.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                    if discount_tax.id in line.tax_ids.ids:
                        line.tax_ids = [(3, discount_tax.id, 0)]
    
    def _get_branch_address(self):
        """Get branch address in a single line format for PDF reports"""
        self.ensure_one()
        company = self.company_id
        address_parts = []
        
        if company.street:
            address_parts.append(company.street)
        if company.street2:
            address_parts.append(company.street2)
        if company.city:
            address_parts.append(company.city)
        if company.state_id:
            address_parts.append(company.state_id.name)
        if company.zip:
            address_parts.append(company.zip)
        if company.country_id:
            address_parts.append(company.country_id.name)
            
        return ', '.join(address_parts)
    
    def _get_vat_12_amount(self):
        """Get VAT 12% amount from taxes (ONLY VAT 12%, excluding withholding taxes)"""
        self.ensure_one()
        vat_12_amount = 0.0
        
        # Method 1: Check tax lines for VAT 12% (most reliable)
        for tax_line in self.line_ids.filtered(lambda line: line.tax_line_id):
            tax = tax_line.tax_line_id
            # Check if this is VAT 12% tax by name pattern and amount
            is_vat_12 = (
                ('VAT' in tax.name.upper() or 'vat' in tax.name.lower() or 'IVA' in tax.name.upper()) and 
                (abs(tax.amount - 12.0) < 0.01 or '12' in tax.name) and
                tax.amount > 0  # Must be positive tax (not withholding)
            )
            if is_vat_12:
                # Use credit for customer invoices, debit for vendor bills
                if self.move_type in ('out_invoice', 'out_refund'):
                    vat_12_amount += tax_line.credit
                else:
                    vat_12_amount += tax_line.debit
        
        # Method 2: If no VAT 12% found, try to calculate from invoice lines
        if vat_12_amount == 0.0:
            for line in self.invoice_line_ids:
                for tax in line.tax_ids:
                    is_vat_12 = (
                        ('VAT' in tax.name.upper() or 'vat' in tax.name.lower() or 'IVA' in tax.name.upper()) and 
                        (abs(tax.amount - 12.0) < 0.01 or '12' in tax.name) and
                        tax.amount > 0  # Must be positive tax
                    )
                    if is_vat_12:
                        # Calculate VAT amount for this line
                        line_subtotal = line.price_subtotal
                        vat_12_amount += line_subtotal * (tax.amount / 100.0)
        
        # Method 3: Calculate based on positive taxes only (exclude negative withholding)
        if vat_12_amount == 0.0:
            positive_tax_amount = 0.0
            for tax_line in self.line_ids.filtered(lambda line: line.tax_line_id):
                tax = tax_line.tax_line_id
                if tax.amount > 0:  # Only positive taxes (VAT, not withholding)
                    if self.move_type in ('out_invoice', 'out_refund'):
                        positive_tax_amount += tax_line.credit
                    else:
                        positive_tax_amount += tax_line.debit
            
            # If we have positive taxes, assume it's VAT
            if positive_tax_amount > 0:
                vat_12_amount = positive_tax_amount
        
        return vat_12_amount
    
    def _get_withholding_tax_amount(self):
        """Calculate withholding tax amount (WHT, WHC, etc.) adjusted for discount"""
        self.ensure_one()
        
        # If there's a discount ID, recalculate withholding tax on discounted amount
        if self.sc_pwd_nac_mov_solo_parent_id_no:
            # Method 1: Find actual withholding tax rate from tax lines
            withholding_rate = 0.0
            for tax_line in self.line_ids.filtered(lambda line: line.tax_line_id):
                tax = tax_line.tax_line_id
                # Check if this is a withholding tax
                is_withholding = (
                    tax.amount < 0 or  # Negative tax rate
                    ('WHT' in tax.name.upper() or 'WHC' in tax.name.upper() or 
                     'withholding' in tax.name.lower() or 'creditable' in tax.name.lower())
                )
                if is_withholding:
                    withholding_rate = abs(tax.amount)  # Get the tax rate (e.g., 2%)
                    break
            
            # If we found a withholding tax rate, apply it to the discounted amount
            if withholding_rate > 0:
                discounted_untaxed = self._get_discounted_untaxed_amount()
                return discounted_untaxed * (withholding_rate / 100.0)
        
        # Method 2: Calculate by summing existing negative taxes (withholding taxes)
        negative_tax_amount = 0.0
        for tax_line in self.line_ids.filtered(lambda line: line.tax_line_id):
            tax = tax_line.tax_line_id
            # Check if this is a withholding tax (negative tax that's not VAT)
            is_withholding = (
                tax.amount < 0 or  # Negative tax rate
                ('WHT' in tax.name.upper() or 'WHC' in tax.name.upper() or 
                 'withholding' in tax.name.lower() or 'creditable' in tax.name.lower())
            )
            if is_withholding:
                negative_tax_amount += abs(tax_line.credit - tax_line.debit)
        
        # If we have withholding taxes and a discount, adjust proportionally
        if negative_tax_amount > 0.01 and self.sc_pwd_nac_mov_solo_parent_id_no:
            # Calculate what the withholding would be on the discounted amount
            original_base = self.amount_untaxed + self._get_discount_amount()  # Original untaxed amount
            if original_base > 0:
                withholding_rate = negative_tax_amount / original_base
                return self._get_discounted_untaxed_amount() * withholding_rate
        
        # Method 3: Formula method (fallback)
        if negative_tax_amount > 0.01:
            return negative_tax_amount
        else:
            # Calculate by formula (Total - Discounted Untaxed - VAT12%)
            vat_12_amount = self._get_vat_12_amount()
            discounted_untaxed = self._get_discounted_untaxed_amount()
            formula_amount = abs(self.amount_total - discounted_untaxed - vat_12_amount)
            
            # If the calculated amount is very small (rounding errors), treat it as zero
            if formula_amount < 0.01:
                formula_amount = 0.0
                
            return formula_amount

    def _debug_tax_info(self):
        """Debug method to see tax calculations"""
        self.ensure_one()
        if self.sc_pwd_nac_mov_solo_parent_id_no:
            discount = self._get_discount_amount()
            discounted_base = self.amount_untaxed - discount
            
            print(f"\n=== DETAILED TAX DEBUG ===")
            print(f"Original Untaxed: ₱{self.amount_untaxed:.4f}")
            print(f"Discount (5%): ₱{discount:.4f}")
            print(f"Discounted Base: ₱{discounted_base:.4f}")
            
            # Check individual tax calculations
            for line in self.line_ids:
                if line.tax_line_id:
                    print(f"Tax Line - {line.tax_line_id.name}: ₱{line.amount_currency:.4f}")
            
            # Check the tax totals structure
            if hasattr(self, 'tax_totals') and self.tax_totals:
                totals = self.tax_totals
                print(f"\n--- Tax Totals Structure ---")
                print(f"Base Amount Currency: ₱{totals.get('base_amount_currency', 0):.4f}")
                print(f"Tax Amount Currency: ₱{totals.get('tax_amount_currency', 0):.4f}")
                print(f"Total Amount Currency: ₱{totals.get('total_amount_currency', 0):.4f}")
                
                if 'subtotals' in totals:
                    for i, subtotal in enumerate(totals['subtotals']):
                        print(f"Subtotal {i} - {subtotal.get('name', 'Unknown')}:")
                        print(f"  Base: ₱{subtotal.get('base_amount_currency', 0):.4f}")
                        print(f"  Tax: ₱{subtotal.get('tax_amount_currency', 0):.4f}")
                        
                        if 'tax_groups' in subtotal:
                            for tax_group in subtotal['tax_groups']:
                                print(f"    {tax_group.get('group_name', 'Unknown Tax')}: ₱{tax_group.get('tax_amount_currency', 0):.4f}")
                
                # Manual calculation
                widget_calculation = totals.get('base_amount_currency', 0)
                for subtotal in totals.get('subtotals', []):
                    if subtotal.get('name') == '5% Discount':
                        widget_calculation += subtotal.get('base_amount_currency', 0)  # This should be negative
                    widget_calculation += subtotal.get('tax_amount_currency', 0)
                
                print(f"\n--- Manual Widget Calculation ---")
                print(f"Calculated Total: ₱{widget_calculation:.4f}")
                print(f"Expected Total: ₱{discounted_base:.4f} + taxes")
            
            print(f"================================\n")
        
        return True
        """Debug method to see all taxes in the invoice"""
        self.ensure_one()
        info = []
        
        # Check invoice line taxes
        info.append("=== Invoice Line Taxes ===")
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                info.append(f"Line Tax: {tax.name}, Amount: {tax.amount}%, Type: {tax.amount_type}")
        
        # Check tax lines in move
        info.append("\n=== Tax Lines in Move ===")
        for line in self.line_ids.filtered(lambda l: l.tax_line_id):
            tax = line.tax_line_id
            info.append(f"Tax Line: {tax.name}, Amount: {tax.amount}%, Credit: {line.credit}, Debit: {line.debit}")
        
        # Show amounts
        info.append(f"\n=== Move Amounts ===")
        info.append(f"Amount Untaxed: {self.amount_untaxed}")
        info.append(f"Amount Tax: {self.amount_tax}")  
        info.append(f"Amount Total: {self.amount_total}")
        
        return "\n".join(info)
