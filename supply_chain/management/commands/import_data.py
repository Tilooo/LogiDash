import pandas as pd
from django.core.management.base import BaseCommand
from supply_chain.models import Supplier, Product, Order
from datetime import datetime


class Command(BaseCommand):
    help = 'Import data from a CSV file into the database'

    def handle(self, *args, **kwargs):
        csv_file_path = 'data/DataCoSupplyChainDataset.csv'
        df = pd.read_csv(csv_file_path, encoding='latin1')

        # old data cleared before importing to prevent create duplicate orders after the scrip run
        self.stdout.write("Clearing old data from the database...")
        Order.objects.all().delete()
        Product.objects.all().delete()
        Supplier.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Old data cleared."))

        self.stdout.write("Starting data import...")

        # a set to keep track of order IDs
        processed_order_ids = set()

        # iterates over each row in the DataFrame
        for index, row in df.iterrows():

            # Create or get the Supplier
            supplier_name = row['Product Name'].split(',')[0]
            supplier, created = Supplier.objects.get_or_create(
                name=supplier_name,
                defaults={
                    'contact_email': 'supplier@example.com',
                    'phone_number': '000-000-0000',
                    'address': '123 Supplier St'
                }
            )

            # Create or get the Product
            product, created = Product.objects.get_or_create(
                sku=row['Product Card Id'],
                defaults={
                    'name': row['Product Name'],
                    'description': row['Product Description'] if pd.notna(
                        row['Product Description']) else 'No description available',
                    'category': row['Category Name'],
                    'supplier': supplier
                }
            )

            # Create the Order
            order_id = row['Order Id']

            # to check if this order have already processed in the loop
            if order_id not in processed_order_ids:
                try:
                    # convert the date string from the CSV into a Python datetime object
                    order_date_obj = datetime.strptime(row['order date (DateOrders)'], '%m/%d/%Y %H:%M')

                    Order.objects.create(
                        order_id=order_id,
                        product=product,
                        customer_city=row['Customer City'],
                        customer_country=row['Customer Country'],
                        order_date=order_date_obj
                    )
                    # the ID to the set to not create it again added
                    processed_order_ids.add(order_id)

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Could not process Order ID {order_id}. Error: {e}"))

        self.stdout.write(
            self.style.SUCCESS(f'Data import complete! Created {len(processed_order_ids)} unique orders.'))