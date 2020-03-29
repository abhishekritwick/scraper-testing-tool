from rest_framework import serializers

class SearchSerializer(serializers.Serializer):
    site        = serializers.CharField(max_length=20)
    search      = serializers.CharField(max_length=20)
    url         = serializers.URLField(max_length=200, allow_blank=True)
    scraperApi  = serializers.URLField(max_length=200, allow_blank=True)
    summary     = serializers.JSONField(True, None)
    issues      = serializers.JSONField(True, None)
    cacheURLs   = serializers.JSONField(True, None)

    def validate(self,data):
        sku = data.get("sku", None)
        if sku == "":
            sku = None
        url = data.get("url", None)
        if sku is None and url is None:
            raise serializers.ValidationError("Sku or Url is required")

        return data
