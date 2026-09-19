#!/usr/bin/env python3
"""Generate deterministic fictional transaction data for the platform demo."""
import argparse
import csv
import random
from pathlib import Path

CLASSES = {
    "TAXABLE_TANGIBLE": {
        "categories": ["office-supplies", "computer-hardware", "furniture"],
        "descriptions": [
            "ergonomic office chair", "business laptop computer",
            "printer toner cartridge", "standing desk",
        ],
        "exempt": "false",
    },
    "TAXABLE_SAAS": {
        "categories": ["software-subscription", "cloud-service"],
        "descriptions": [
            "annual accounting software subscription",
            "monthly hosted analytics platform",
            "cloud document automation license",
            "SaaS compliance reporting seats",
        ],
        "exempt": "false",
    },
    "EXEMPT_PROFESSIONAL_SERVICE": {
        "categories": ["consulting", "professional-service", "training"],
        "descriptions": [
            "tax advisory consulting engagement",
            "implementation professional services",
            "onsite product training",
            "compliance process assessment",
        ],
        "exempt": "true",
    },
}
STATES = ["CA", "FL", "MA", "NY", "TX", "WA"]
CUSTOMERS = ["commercial", "government", "nonprofit"]


def generate(rows, seed=20260919):
    randomizer = random.Random(seed)
    labels = list(CLASSES)
    records = []
    for index in range(rows):
        label = labels[index % len(labels)]
        profile = CLASSES[label]
        records.append({
            "transaction_id": f"MOCK-{index + 1:06d}",
            "item_description": randomizer.choice(profile["descriptions"]),
            "product_category": randomizer.choice(profile["categories"]),
            "amount": f"{randomizer.uniform(25, 5000):.2f}",
            "destination_state": randomizer.choice(STATES),
            "exemption_certificate": profile["exempt"],
            "customer_type": randomizer.choice(CUSTOMERS),
            "label": label,
        })
    randomizer.shuffle(records)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows", type=int, default=600)
    parser.add_argument("--seed", type=int, default=20260919)
    args = parser.parse_args()
    if args.rows < 30:
        parser.error("rows must be at least 30")
    records = generate(args.rows, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=records[0])
        writer.writeheader()
        writer.writerows(records)
    print(f"Wrote {len(records)} synthetic rows to {args.output}")


if __name__ == "__main__":
    main()
