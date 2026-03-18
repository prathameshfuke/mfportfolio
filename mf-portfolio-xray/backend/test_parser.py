from parser import parse_cams_pdf

with open("mock_cams_statement.pdf", "rb") as f:
    result = parse_cams_pdf(f.read())

for fund in result:
    print(f"\nFund: {fund['fund_name']}")
    print(f"  Transactions: {len(fund['transactions'])}")
    print(f"  Closing units: {fund['closing_units']}")
    print(f"  Market value: {fund['market_value']}")
    if fund['transactions']:
        print(f"  First txn: {fund['transactions'][0]}")
        print(f"  Last txn:  {fund['transactions'][-1]}")
