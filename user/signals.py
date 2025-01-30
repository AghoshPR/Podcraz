#offer apply


from django.db.models.signals import *
from django.dispatch import *
from django.utils.timezone import now
from . models import *


@receiver(post_save, sender=Offer)
def apply_discount(sender, instance, created, **kwargs):
    
    
    if instance.is_active and instance.valid_from <= now() <= instance.valid_until:
        variants = []
        if instance.product:
            variants = ProductVariant.objects.filter(product=instance.product)
        elif instance.product_category:
            variants = ProductVariant.objects.filter(product__product_category=instance.product_category)
        
        for variant in variants:
            if instance.discount_type == 'percentage':
                discount = variant.price * Decimal(str(instance.discount_value)) / 100
                variant.discounted_price = variant.price - discount
            else:  # fixed amount
                variant.discounted_price = variant.price - Decimal(str(instance.discount_value))
            variant.save()


@receiver(post_delete, sender=Offer)
def remove_offer_discount(sender, instance, **kwargs):
    if instance.product:
        variants = ProductVariant.objects.filter(product=instance.product)
    elif instance.product_category:
        variants = ProductVariant.objects.filter(product__product_category=instance.product_category)
    else:
        variants = []

    for variant in variants:
        variant.remove_discount()