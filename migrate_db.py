#!/usr/bin/env python3
"""
Database migration script to add customization fields to Product model.
Run this after updating the models.py file.
"""

import os
from app import create_app, db

def migrate_database():
    """Add new columns to existing database"""
    app = create_app()

    with app.app_context():
        # Check if columns exist, if not add them
        inspector = db.inspect(db.engine)

        columns = inspector.get_columns('product')

        column_names = [col['name'] for col in columns]

        # Add new columns if they don't exist
        with db.engine.connect() as conn:
            if 'is_customized' not in column_names:
                print("Adding is_customized column...")
                conn.execute(db.text("ALTER TABLE product ADD COLUMN is_customized BOOLEAN DEFAULT FALSE"))
                conn.commit()

            if 'customization_type' not in column_names:
                print("Adding customization_type column...")
                conn.execute(db.text("ALTER TABLE product ADD COLUMN customization_type VARCHAR(50)"))
                conn.commit()

            if 'customization_details' not in column_names:
                print("Adding customization_details column...")
                conn.execute(db.text("ALTER TABLE product ADD COLUMN customization_details TEXT"))
                conn.commit()

            if 'base_product_id' not in column_names:
                print("Adding base_product_id column...")
                conn.execute(db.text("ALTER TABLE product ADD COLUMN base_product_id INTEGER REFERENCES product(id)"))
                conn.commit()

        print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_database()