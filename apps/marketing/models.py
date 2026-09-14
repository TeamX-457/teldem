from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class ContactSubmission(models.Model):
    class InterestType(models.TextChoices):
        B2C = "b2c", "Individual / Household"
        B2B = "b2b", "Business / Organization"

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=32, blank=True)
    interest_type = models.CharField(max_length=10, choices=InterestType.choices)
    company_name = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_contacted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_interest_type_display()})"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    cover_image = models.ImageField(upload_to="blog/covers/", blank=True, null=True)
    excerpt = models.CharField(max_length=280, blank=True)
    body = models.TextField()
    author_name = models.CharField(max_length=100, default="TELDEM Team")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)[:200]
            slug = base_slug
            counter = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("marketing:blog_detail", kwargs={"slug": self.slug})
