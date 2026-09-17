#!/usr/bin/env python3

import argparse
import csv
import random
from pathlib import Path


TEMPLATES = {
    "W-2": [
        (
            "Form W-2 Wage and Tax Statement. Employer {company}. "
            "Employer EIN {ein}. Employee wages {amount}. "
            "Federal income tax withheld {tax}. "
            "Social Security wages and Medicare wages reported."
        ),
        (
            "W-2 employee wage statement for tax year 2025. "
            "Employer {company}. EIN {ein}. "
            "Wages tips and other compensation {amount}. "
            "Federal tax withheld {tax}."
        ),
        (
            "Annual wage statement Form W-2 from {company}. "
            "Employer identification number {ein}. "
            "Taxable wages {amount}; federal withholding {tax}."
        ),
    ],

    "1099-NEC": [
        (
            "Form 1099-NEC Nonemployee Compensation. "
            "Payer {company}. Payer TIN {ein}. "
            "Box 1 nonemployee compensation {amount}. "
            "Federal income tax withheld {tax}."
        ),
        (
            "1099-NEC contractor tax statement issued by {company}. "
            "Nonemployee compensation {amount}. "
            "Payer tax identification number {ein}."
        ),
        (
            "Independent contractor Form 1099-NEC. "
            "Payer {company}; TIN {ein}; "
            "nonemployee compensation box 1 {amount}."
        ),
    ],

    "1099-MISC": [
        (
            "Form 1099-MISC Miscellaneous Information. "
            "Payer {company}. Payer TIN {ein}. "
            "Rents and miscellaneous income reported. "
            "Amount {amount}."
        ),
        (
            "1099-MISC statement from {company}. "
            "Miscellaneous income {amount}. "
            "Rents royalties and other income fields present. "
            "TIN {ein}."
        ),
        (
            "Tax document Form 1099-MISC. "
            "Payer {company}; identifier {ein}; "
            "miscellaneous information amount {amount}."
        ),
    ],

    "INVOICE": [
        (
            "Invoice {doc_number}. Vendor {company}. "
            "Invoice date 2026-{month:02d}-{day:02d}. "
            "Subtotal {amount}. Sales tax {tax}. "
            "Amount due {total}. Payment terms net 30."
        ),
        (
            "Customer invoice number {doc_number} from {company}. "
            "Services rendered. Subtotal {amount}; tax {tax}; "
            "balance due {total}."
        ),
        (
            "INVOICE {doc_number}. Bill from {company}. "
            "Line items, quantity, unit price and amount due {total}. "
            "Payment terms included."
        ),
    ],

    "RECEIPT": [
        (
            "Receipt {doc_number}. Merchant {company}. "
            "Transaction date 2026-{month:02d}-{day:02d}. "
            "Purchase amount {amount}. Tax {tax}. "
            "Total paid {total}. Payment approved."
        ),
        (
            "Sales receipt from {company}. "
            "Receipt number {doc_number}. "
            "Items purchased and total payment {total}. "
            "Card transaction completed."
        ),
        (
            "Purchase receipt {doc_number}. Store {company}. "
            "Subtotal {amount}; sales tax {tax}; total {total}. "
            "Thank you for your purchase."
        ),
    ],

    "OTHER": [
        (
            "Internal project memo {doc_number}. "
            "Team meeting notes for {company}. "
            "Discuss platform milestones, action items, "
            "operations review and engineering priorities."
        ),
        (
            "Engineering status report {doc_number}. "
            "Application reliability review for {company}. "
            "Topics include Kubernetes capacity, deployment status, "
            "monitoring and incident follow-up."
        ),
        (
            "General correspondence document {doc_number}. "
            "Message regarding scheduling, project planning, "
            "team responsibilities and operational updates."
        ),
    ],
}


COMPANIES = [
    "Northstar Services LLC",
    "Pine Valley Consulting",
    "Sunrise Technology Group",
    "Blue River Solutions",
    "Atlas Business Services",
    "Evergreen Professional Group",
    "Harbor Point Systems",
    "Cypress Digital Services",
]


def money(rng, minimum, maximum):
    value = rng.uniform(minimum, maximum)
    return f"${value:,.2f}"


def generate_text(label, index, rng):
    template = rng.choice(TEMPLATES[label])

    company = rng.choice(COMPANIES)

    ein = (
        f"{rng.randint(10, 99)}-"
        f"{rng.randint(1000000, 9999999)}"
    )

    amount_value = rng.uniform(500, 95000)
    tax_value = amount_value * rng.uniform(0.04, 0.24)
    total_value = amount_value + tax_value

    values = {
        "company": company,
        "ein": ein,
        "amount": f"${amount_value:,.2f}",
        "tax": f"${tax_value:,.2f}",
        "total": f"${total_value:,.2f}",
        "doc_number": f"DOC-{index:06d}",
        "month": rng.randint(1, 12),
        "day": rng.randint(1, 28),
    }

    return template.format(**values)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        default="/app/data/tax_documents.csv",
    )

    parser.add_argument(
        "--rows-per-class",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    rng = random.Random(42)

    rows = []
    sequence = 1

    for label in TEMPLATES:
        for class_index in range(args.rows_per_class):
            rows.append(
                {
                    "document_id": (
                        f"{label.lower().replace('-', '_')}"
                        f"-{class_index + 1:04d}"
                    ),
                    "text": generate_text(
                        label,
                        sequence,
                        rng,
                    ),
                    "label": label,
                }
            )

            sequence += 1

    rng.shuffle(rows)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "document_id",
                "text",
                "label",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Generated {len(rows)} synthetic documents "
        f"at {output}"
    )

    print(
        f"Classes: {', '.join(TEMPLATES.keys())}"
    )


if __name__ == "__main__":
    main()
