import pandas as pd
from django.core.management.base import BaseCommand
from supply_chain.models import Supplier, Product


class Command(BaseCommand):
    help = 'Import data from a CSV file into the database'

    def handle(self, *args, **kwargs):
        csv_file_path = 'data/DataCoSupplyChainDataset.csv'
        df = pd.read_csv(csv_file_path, encoding='latin1')  # read the CSV file using pandas,holding errors

        self.stdout.write("Starting data import...")

        for index, row in df.iterrows():  # iterate over each row in the DataFrame
            # --- Create or get the Supplier ---
            supplier_name = row['Product Name'].split(',')[0]  # to get a supplier name
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_name,
                defaults={
                    'contact_email': 'supplier@example.com',
                    'phone_number': '000-000-0000',
                    'address': '123 Supplier St'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'New supplier created: {supplier.name}'))

            # --- Create or get the Product ---
            product, created = Product.objects.get_or_create(
                sku=row['Product Card Id'],
                defaults={
                    'name': row['Product Name'],
                    'description': row['Product Description'] if pd.notna(
                        row['Product Description']) else 'No description available',
                    'supplier': supplier
                }
            )

        self.stdout.write(self.style.SUCCESS('Data import complete!'))