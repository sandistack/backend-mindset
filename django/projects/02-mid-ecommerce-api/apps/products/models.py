"""
Product catalog models: Category, Product, ProductVariant, ProductImage.
"""

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal


# ============================================
# CATEGORY MODEL
# ============================================

class CategoryManager(models.Manager):
    """Custom manager for Category."""
    
    def active(self):
        """Return only active categories."""
        return self.filter(is_active=True)
    
    def root_categories(self):
        """Return top-level categories (no parent)."""
        return self.filter(parent=None, is_active=True)


class Category(models.Model):
    """Product category with nested structure (parent-child)."""
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CategoryManager()
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        db_table = 'categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_ancestors(self):
        """Get all parent categories up to root."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        """Get all child categories recursively."""
        descendants = []
        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_full_path(self):
        """Return full category path: 'Electronics > Phones > Smartphones'."""
        ancestors = self.get_ancestors()
        path = ' > '.join([cat.name for cat in ancestors] + [self.name])
        return path


# ============================================
# PRODUCT MODEL
# ============================================

class ProductManager(models.Manager):
    """Custom manager for Product."""
    
    def active(self):
        """Return only active products."""
        return self.filter(is_active=True)
    
    def featured(self):
        """Return featured products."""
        return self.filter(is_active=True, is_featured=True)


class Product(models.Model):
    """Main product model."""
    
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, 
        related_name='products'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProductManager()
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'products'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def primary_image(self):
        """Get primary product image, or first image if no primary set."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()
    
    @property
    def price_range(self):
        """Get min and max price from all variants."""
        variants = self.variants.filter(is_active=True)
        if not variants.exists():
            return {'min': self.base_price, 'max': self.base_price}
        
        prices = variants.values_list('price', flat=True)
        return {
            'min': min(prices) if prices else self.base_price,
            'max': max(prices) if prices else self.base_price
        }
    
    @property
    def total_stock(self):
        """Get total stock from all variants."""
        total = self.variants.filter(is_active=True).aggregate(
            total=models.Sum('stock')
        )['total']
        return total or 0
    
    @property
    def is_in_stock(self):
        """Check if product has any stock available."""
        return self.total_stock > 0


# ============================================
# PRODUCT VARIANT MODEL
# ============================================

class ProductVariant(models.Model):
    """Product variant (size, color, etc) with individual pricing and stock."""
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='variants'
    )
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, help_text="e.g., 'Red - Large'")
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Override base price if different"
    )
    stock = models.PositiveIntegerField(default=0)
    weight = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Weight in kg for shipping calculation"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        db_table = 'product_variants'
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def is_in_stock(self):
        """Check if variant has stock available."""
        return self.stock > 0
    
    def reserve_stock(self, quantity):
        """Reserve stock for order. Raises ValueError if insufficient stock."""
        if quantity > self.stock:
            raise ValueError(f"Insufficient stock. Available: {self.stock}, Requested: {quantity}")
        self.stock -= quantity
        self.save(update_fields=['stock'])
    
    def release_stock(self, quantity):
        """Release reserved stock (when order cancelled)."""
        self.stock += quantity
        self.save(update_fields=['stock'])


# ============================================
# PRODUCT IMAGE MODEL
# ============================================

class ProductImage(models.Model):
    """Product images with ordering."""
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        db_table = 'product_images'
    
    def __str__(self):
        return f"{self.product.name} - Image {self.order}"
    
    def save(self, *args, **kwargs):
        """If this is set as primary, unset other primary images for this product."""
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
