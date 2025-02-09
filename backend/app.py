[Previous code remains the same...]

    def _format_product_data(self, data: Dict) -> str:
        """Format real-time product data for GPT context"""
        if not data or not data.get('product'):
            return "\nProduct data unavailable"
            
        context = "\nReal-time product information:"
        
        # Basic product info
        product = data.get('product', {})
        if product:
            context += f"\nProduct: {product.get('title', 'N/A')}"
            context += f"\nStyle: {product.get('style', 'N/A')}"
            context += f"\nBrand: {product.get('brand', 'N/A')}"
            context += f"\nDescription: {product.get('description', 'N/A')}"
            
            # Format color information more clearly
            if product.get('colors'):
                context += "\nAvailable Colors:"
                green_colors = []
                other_colors = []
                for color in product['colors']:
                    if 'green' in color.lower():
                        green_colors.append(color)
                    else:
                        other_colors.append(color)
                
                if green_colors:
                    context += f"\n- Green Options: {', '.join(green_colors)}"
                context += f"\n- Other Colors: {', '.join(other_colors[:5])}..."
            
            if product.get('available_sizes'):
                context += f"\nAvailable Sizes: {', '.join(product['available_sizes'])}"
        
        # Pricing info with bulk pricing if available
        pricing = data.get('pricing', {})
        if pricing:
            context += f"\nPricing:"
            context += f"\n- Regular Price: ${pricing.get('piece_price', 'N/A')}"
            if pricing.get('case_price'):
                context += f"\n- Case Price: ${pricing.get('case_price')} (bulk pricing)"
            if pricing.get('sale_price'):
                context += f"\n- Sale Price: ${pricing.get('sale_price')}"
            if pricing.get('price_text'):
                context += f"\n- {pricing.get('price_text')}"
        
        # Format inventory information by size
        inventory = data.get('inventory', {})
        if inventory:
            total_available = sum(inv.get('total_available', 0) for inv in inventory.values())
            context += f"\nTotal Available: {total_available} units"
            context += "\nInventory by Size:"
            
            for size, inv in inventory.items():
                total = inv.get('total_available', 0)
                if total > 0:
                    context +=