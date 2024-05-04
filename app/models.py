from django.db import models


class URLRedirect(models.Model):
    url = models.URLField(unique=True)
    hit_count = models.IntegerField(default=0)

    @classmethod
    def hit(cls, url):
        obj, created = cls.objects.get_or_create(url=url)
        obj.hit_count += 1
        obj.save()