from rest_framework import serializers

class ProductSerializer(serializers.Serializer):
    site        = serializers.CharField(max_length=20)
    sku         = serializers.CharField(max_length=50)
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

class FetchSkuSerializer(serializers.Serializer):
    skus        = serializers.CharField(max_length=50)
    def validate(self, data):
        sku = data.get("skus", None)
        if sku == "" or sku is None:
            raise serializers.ValidationError("Skus are missing")

        return data

class FetchMetadataSerializer(serializers.Serializer):
    metadata        = serializers.JSONField(True, None)

    
