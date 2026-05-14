from pathlib import Path

path = Path('app.py')
text = path.read_text()
old = '''            base_product = Product.query.get_or_404(base_product_id)
            
            # Generate unique SKU
            import re
            safe_name = re.sub(r'[^\\w\\-]', '', name.replace(' ', '-'))
            custom_sku = f"{base_product.sku}-CUSTOM-{safe_name.upper()}"
            
            # Check if SKU exists
            if Product.query.filter_by(sku=custom_sku).first():
                flash('A customized product with this name already exists.', 'danger')
                return redirect(url_for('customized_necklaces'))
            
            # Create customized product
'''
new = '''            base_product = Product.query.get_or_404(base_product_id)
            
            import re
            def make_sku(custom_name):
                safe_name = re.sub(r'[^A-Za-z0-9]+', '-', custom_name.strip())
                safe_name = re.sub(r'-{2,}', '-', safe_name).strip('-')
                return f"{base_product.sku}-CUSTOM-{safe_name.upper()}"

            if paste_names.strip():
                names = [line.strip() for line in re.split(r'[\\r\\n,;]+', paste_names) if line.strip()]
                if not names:
                    flash('Please enter at least one name in the bulk paste field.', 'danger')
                    return redirect(url_for('customized_necklaces'))

                counts = {}
                for custom_name in names:
                    counts[custom_name] = counts.get(custom_name, 0) + 1

                created = 0
                updated = 0
                for custom_name, count in counts.items():
                    custom_sku = make_sku(custom_name)
                    product = Product.query.filter_by(sku=custom_sku).first()
                    if product:
                        product.current_stock += count
                        updated += 1
                    else:
                        product = Product(
                            sku=custom_sku,
                            name=f"{base_product.name} - {custom_name}",
                            description=f"Customized {base_product.name} with name: {custom_name}",
                            cost_price=base_product.cost_price,
                            selling_price=base_product.selling_price,
                            current_stock=count,
                            reorder_level=0,
                            is_active=True,
                            is_customized=True,
                            customization_type='necklace',
                            customization_details=json.dumps({'name': custom_name}),
                            base_product_id=base_product.id
                        )
                        db.session.add(product)
                        db.session.flush()
                        created += 1

                    movement = StockMovement(
                        product_id=product.id,
                        movement_type='add',
                        quantity=count,
                        reason='customization',
                        reference_number=custom_sku,
                        user_id=current_user.id,
                        notes=f'Bulk customized necklace entry for {custom_name}'
                    )
                    db.session.add(movement)

                db.session.commit()
                flash(f'Bulk custom names processed: {created} created, {updated} updated.', 'success')
                return redirect(url_for('customized_necklaces'))

            if name.strip():
                custom_name = name.strip()
                custom_sku = make_sku(custom_name)
                if Product.query.filter_by(sku=custom_sku).first():
                    flash('A customized product with this name already exists.', 'danger')
                    return redirect(url_for('customized_necklaces'))

                custom_product = Product(
'''
if old not in text:
    print('Old block not found.')
    start = text.find('base_product = Product.query.get_or_404(base_product_id)')
    end = text.find('# Get base products (non-customized necklaces)')
    print(text[start:end])
else:
    path.write_text(text.replace(old, new, 1))
    print('Patch applied successfully.')
