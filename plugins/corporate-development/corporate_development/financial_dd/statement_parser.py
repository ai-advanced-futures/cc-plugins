"""
Financial statement parser - placeholder implementation.

This module will handle parsing and validation of financial statements from CSV/JSON.
Full implementation will be added in a future task.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from decimal import Decimal
from datetime import date, datetime
import pandas as pd
import json

from corporate_development.financial_dd.types import (
    IncomeStatement, ValidationResult, ParseResult
)


class StatementParser:
    """Parser for financial statements from CSV and JSON formats."""

    # Currency symbol to ISO code mapping
    CURRENCY_SYMBOLS = {
        '$': 'USD',
        '€': 'EUR',
        '£': 'GBP',
        '¥': 'JPY',
    }

    # ISO codes we support
    CURRENCY_CODES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY']

    # Synonym dictionaries for column mapping
    INCOME_STATEMENT_SYNONYMS = {
        'revenue': ['revenue', 'sales', 'total_revenue', 'gross_sales',
                    'net_sales', 'turnover', 'income', 'total_sales'],
        'cogs': ['cogs', 'cost_of_goods_sold', 'cost_of_sales',
                 'direct_costs', 'cost_of_revenue'],
        'operating_expenses': ['operating_expenses', 'opex', 'operating_costs',
                               'sg&a', 'sga', 'admin_expenses', 'general_expenses'],
        'depreciation': ['depreciation', 'depreciation_expense', 'd&a',
                        'depreciation_amortization'],
        'amortization': ['amortization', 'amortization_expense'],
        'interest_expense': ['interest_expense', 'interest', 'interest_paid',
                            'finance_costs', 'interest_costs'],
        'tax_expense': ['tax_expense', 'taxes', 'income_tax', 'tax',
                       'income_taxes', 'tax_provision'],
    }

    BALANCE_SHEET_SYNONYMS = {
        'cash': ['cash', 'cash_and_equivalents', 'cash_equivalents',
                 'cash_balance', 'cash_on_hand'],
        'accounts_receivable': ['accounts_receivable', 'receivables', 'ar',
                               'trade_receivables', 'debtors'],
        'inventory': ['inventory', 'stock', 'inventories'],
        'current_assets': ['current_assets', 'total_current_assets'],
        'ppe_net': ['ppe_net', 'property_plant_equipment', 'ppe', 'fixed_assets'],
        'intangibles': ['intangibles', 'intangible_assets'],
        'accounts_payable': ['accounts_payable', 'payables', 'ap',
                            'trade_payables', 'creditors'],
        'current_liabilities': ['current_liabilities', 'total_current_liabilities'],
        'long_term_debt': ['long_term_debt', 'lt_debt', 'long_term_liabilities'],
        'equity': ['equity', 'shareholders_equity', 'owners_equity',
                  'stockholders_equity', 'net_worth'],
    }

    CASH_FLOW_SYNONYMS = {
        'operating_cash_flow': ['operating_cash_flow', 'cash_from_operations',
                               'ocf', 'cfo', 'operating_activities'],
        'investing_cash_flow': ['investing_cash_flow', 'cash_from_investing',
                               'investing_activities', 'cfi'],
        'financing_cash_flow': ['financing_cash_flow', 'cash_from_financing',
                               'financing_activities', 'cff'],
    }

    def __init__(self):
        """Initialize the statement parser."""
        # Build reverse lookup dictionary for fast mapping
        self._column_map = {}
        for synonyms_dict in [self.INCOME_STATEMENT_SYNONYMS,
                              self.BALANCE_SHEET_SYNONYMS,
                              self.CASH_FLOW_SYNONYMS]:
            for canonical, synonyms in synonyms_dict.items():
                for synonym in synonyms:
                    self._column_map[synonym.lower()] = canonical

    def _normalize_column_name(self, name: str) -> str:
        """Normalize column name for matching.

        Args:
            name: Input column name

        Returns:
            Normalized column name
        """
        # Lowercase, remove special chars, replace spaces with underscores
        normalized = name.lower().strip()
        normalized = normalized.replace(' ', '_')
        normalized = normalized.replace('-', '_')
        # Remove common prefixes/suffixes
        for prefix in ['total_', 'net_']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
        for suffix in ['_amount', '_value']:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized

    def _map_column(self, column_name: str) -> Optional[str]:
        """Map input column name to canonical field name.

        Args:
            column_name: Input column name from file

        Returns:
            Canonical field name or None if unmapped
        """
        normalized = self._normalize_column_name(column_name)
        return self._column_map.get(normalized)

    def _detect_currency_from_symbol(self, text: str) -> str:
        """Detect currency from symbols in text.

        Args:
            text: Text that may contain currency symbols

        Returns:
            ISO currency code (default: USD)
        """
        if not text:
            return "USD"

        for symbol, code in self.CURRENCY_SYMBOLS.items():
            if symbol in text:
                return code

        return "USD"

    def _detect_currency_from_text(self, text: str) -> str:
        """Detect currency from ISO codes in text.

        Args:
            text: Text that may contain ISO currency codes

        Returns:
            ISO currency code (default: USD)
        """
        if not text:
            return "USD"

        # Look for ISO codes (3-letter uppercase)
        text_upper = text.upper()
        for code in self.CURRENCY_CODES:
            if code in text_upper:
                return code

        return "USD"

    def _detect_currency(
        self,
        column_names: list,
        sample_values: Dict[str, Any]
    ) -> str:
        """Detect currency from column names and sample values.

        Priority:
        1. Explicit currency column
        2. Currency symbol in column names
        3. Currency symbol in sample values
        4. Default to USD

        Args:
            column_names: List of column names
            sample_values: Dict of column_name -> sample value

        Returns:
            ISO currency code
        """
        # Check for explicit currency column
        for col in column_names:
            if 'currency' in col.lower():
                if col in sample_values:
                    return self._detect_currency_from_text(str(sample_values[col]))

        # Check column names for currency indicators
        for col in column_names:
            currency = self._detect_currency_from_symbol(col)
            if currency != "USD":  # Found non-default
                return currency
            currency = self._detect_currency_from_text(col)
            if currency != "USD":
                return currency

        # Check sample values for currency indicators
        for value in sample_values.values():
            if value:
                currency = self._detect_currency_from_symbol(str(value))
                if currency != "USD":
                    return currency

        return "USD"

    def _parse_date(self, value) -> Optional[date]:
        """Parse date from various formats."""
        if pd.isna(value):
            return None

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(value).date()
            except ValueError:
                try:
                    # Try pandas date parser
                    return pd.to_datetime(value).date()
                except Exception:
                    return None

        return None

    def _to_decimal(self, value) -> Decimal:
        """Convert value to Decimal."""
        if pd.isna(value):
            return Decimal("0")
        return Decimal(str(value))

    def _to_decimal_optional(self, value) -> Optional[Decimal]:
        """Convert value to Decimal or None."""
        if pd.isna(value):
            return None
        return Decimal(str(value))

    def _calculate_validation(
        self,
        income_statements: list,
        balance_sheets: list,
        cash_flow_statements: list,
        mapped_fields: Dict[str, str],
        unmapped_fields: list
    ) -> ValidationResult:
        """Calculate validation result and completeness score."""
        missing_fields = []
        warnings = []
        suggestions = []

        # Check required fields for income statement
        if income_statements:
            stmt = income_statements[0]
            if stmt.revenue == 0:
                missing_fields.append("revenue")
            if stmt.cogs == 0 and stmt.operating_expenses == 0:
                warnings.append("Neither COGS nor operating expenses provided")
        else:
            missing_fields.append("income_statement")

        # Calculate completeness score
        required_count = 2  # revenue, (cogs OR opex)
        required_present = 0

        if income_statements and income_statements[0].revenue > 0:
            required_present += 1
        if income_statements and (income_statements[0].cogs > 0 or income_statements[0].operating_expenses > 0):
            required_present += 1

        required_score = (required_present / required_count) * 60 if required_count > 0 else 0

        # Recommended fields
        recommended_count = 4  # depreciation, amortization, interest, tax
        recommended_present = 0
        if income_statements:
            stmt = income_statements[0]
            if stmt.depreciation and stmt.depreciation > 0:
                recommended_present += 1
            else:
                missing_fields.append("depreciation")
            if stmt.amortization and stmt.amortization > 0:
                recommended_present += 1
            else:
                missing_fields.append("amortization")
            if stmt.interest_expense > 0:
                recommended_present += 1
            if stmt.tax_expense > 0:
                recommended_present += 1

        recommended_score = (recommended_present / recommended_count) * 20 if recommended_count > 0 else 0

        # Quality score (placeholder for now)
        quality_score = 20

        completeness_score = required_score + recommended_score + quality_score

        # Generate suggestions for unmapped fields
        for unmapped in unmapped_fields:
            suggestions.append(f"Unmapped field '{unmapped}' - consider renaming if it contains financial data")

        return ValidationResult(
            is_complete=completeness_score >= 80.0,
            completeness_score=completeness_score,
            missing_fields=missing_fields,
            warnings=warnings,
            suggestions=suggestions,
            mapped_fields=mapped_fields,
            unmapped_fields=unmapped_fields
        )

    def _parse_csv(self, file_path: str) -> ParseResult:
        """Parse financial statements from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            ParseResult with parsed statements and validation
        """
        # Read CSV with pandas
        df = pd.read_csv(file_path)

        # Normalize column names
        df.columns = [self._normalize_column_name(col) for col in df.columns]

        # Detect currency
        sample_values = df.iloc[0].to_dict() if len(df) > 0 else {}
        currency = self._detect_currency(list(df.columns), sample_values)

        # Map columns to canonical names
        mapped_fields = {}
        unmapped_fields = []
        for col in df.columns:
            canonical = self._map_column(col)
            if canonical:
                mapped_fields[col] = canonical
                # Rename column in dataframe
                df.rename(columns={col: canonical}, inplace=True)
            else:
                unmapped_fields.append(col)

        # Parse income statements (row-per-period layout)
        income_statements = []
        for _, row in df.iterrows():
            # Check if this row has income statement fields
            if 'revenue' in row and pd.notna(row['revenue']):
                # Parse dates
                period_start = self._parse_date(row.get('period_start'))
                period_end = self._parse_date(row.get('period_end'))

                if not period_start:
                    period_start = date(2024, 1, 1)  # Default
                if not period_end:
                    period_end = date(2024, 12, 31)  # Default

                # Build income statement
                stmt = IncomeStatement(
                    period_start=period_start,
                    period_end=period_end,
                    revenue=self._to_decimal(row.get('revenue', 0)),
                    cogs=self._to_decimal(row.get('cogs', 0)),
                    operating_expenses=self._to_decimal(row.get('operating_expenses', 0)),
                    depreciation=self._to_decimal_optional(row.get('depreciation')),
                    amortization=self._to_decimal_optional(row.get('amortization')),
                    interest_expense=self._to_decimal(row.get('interest_expense', 0)),
                    tax_expense=self._to_decimal(row.get('tax_expense', 0)),
                    currency=currency
                )
                income_statements.append(stmt)

        # Calculate validation score
        validation = self._calculate_validation(
            income_statements=income_statements,
            balance_sheets=[],
            cash_flow_statements=[],
            mapped_fields=mapped_fields,
            unmapped_fields=unmapped_fields
        )

        return ParseResult(
            income_statements=income_statements,
            balance_sheets=[],  # Will implement in future task
            cash_flow_statements=[],  # Will implement in future task
            validation=validation,
            currency=currency
        )

    def _parse_json(self, file_path: str) -> ParseResult:
        """Parse financial statements from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            ParseResult with parsed statements and validation
        """
        # Read JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            # Array of period objects
            return self._parse_json_array(data)
        elif isinstance(data, dict):
            # Nested structure or single period
            return self._parse_json_dict(data)
        else:
            raise ValueError("JSON must be array or object")

    def _parse_json_array(self, data: list) -> ParseResult:
        """Parse JSON array format (list of period objects)."""
        income_statements = []

        # Detect currency from first record
        sample_values = data[0] if data else {}
        currency = self._detect_currency(
            list(sample_values.keys()),
            sample_values
        )

        mapped_fields = {}
        unmapped_fields = []

        for record in data:
            # Map fields
            mapped_record = {}
            for key, value in record.items():
                canonical = self._map_column(key)
                if canonical:
                    mapped_record[canonical] = value
                    mapped_fields[key] = canonical
                else:
                    unmapped_fields.append(key)

            # Parse period (try various field names)
            period_start = None
            period_end = None

            if 'period_start' in mapped_record:
                period_start = self._parse_date(mapped_record['period_start'])
            elif 'period' in record:
                # Single year/period field
                year = int(record['period'])
                period_start = date(year, 1, 1)
                period_end = date(year, 12, 31)

            if not period_start:
                period_start = date(2024, 1, 1)
            if not period_end:
                if 'period_end' in mapped_record:
                    period_end = self._parse_date(mapped_record['period_end'])
                else:
                    period_end = date(2024, 12, 31)

            # Build income statement if has revenue
            if 'revenue' in mapped_record:
                stmt = IncomeStatement(
                    period_start=period_start,
                    period_end=period_end,
                    revenue=self._to_decimal(mapped_record.get('revenue', 0)),
                    cogs=self._to_decimal(mapped_record.get('cogs', 0)),
                    operating_expenses=self._to_decimal(mapped_record.get('operating_expenses', 0)),
                    depreciation=self._to_decimal_optional(mapped_record.get('depreciation')),
                    amortization=self._to_decimal_optional(mapped_record.get('amortization')),
                    interest_expense=self._to_decimal(mapped_record.get('interest_expense', 0)),
                    tax_expense=self._to_decimal(mapped_record.get('tax_expense', 0)),
                    currency=currency
                )
                income_statements.append(stmt)

        # Calculate validation
        validation = self._calculate_validation(
            income_statements=income_statements,
            balance_sheets=[],
            cash_flow_statements=[],
            mapped_fields=mapped_fields,
            unmapped_fields=list(set(unmapped_fields))
        )

        return ParseResult(
            income_statements=income_statements,
            balance_sheets=[],
            cash_flow_statements=[],
            validation=validation,
            currency=currency
        )

    def _parse_json_dict(self, data: dict) -> ParseResult:
        """Parse JSON dict format (nested structure or single period)."""
        # Check if it has nested income_statement
        if 'income_statement' in data:
            # Flatten nested structure
            income_data = data['income_statement']
            return self._parse_json_array([income_data])
        else:
            # Assume flat single-period structure
            return self._parse_json_array([data])

    def validate_completeness(
        self,
        statements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that all required financial statement components are present.

        Args:
            statements: Financial statements to validate

        Returns:
            Validation results with missing fields and completeness score
        """
        # Placeholder implementation
        return {
            "is_complete": True,
            "missing_fields": [],
            "completeness_score": 1.0,
            "warnings": []
        }

    def parse_statements(
        self,
        file_path: str,
        file_format: Optional[str] = None
    ) -> ParseResult:
        """Parse financial statements from file.

        Args:
            file_path: Path to the statement file
            file_format: Format of the file ("csv" or "json"), auto-detected if None

        Returns:
            ParseResult with statements and validation
        """
        # Auto-detect format if not specified
        if file_format is None:
            ext = Path(file_path).suffix.lower()
            if ext == '.csv':
                file_format = 'csv'
            elif ext == '.json':
                file_format = 'json'
            else:
                raise ValueError(f"Cannot auto-detect format for extension: {ext}")

        # Parse based on format
        if file_format == 'csv':
            return self._parse_csv(file_path)
        elif file_format == 'json':
            return self._parse_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
