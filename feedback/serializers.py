# feedback/serializers.py
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Suggestion, BugReport, Upvote

class SuggestionSerializer(serializers.ModelSerializer):
    votes = serializers.SerializerMethodField()
    class Meta:
        model = Suggestion
        fields = ['id','name','category','description','created_at','votes']

    @extend_schema_field(serializers.IntegerField())
    def get_votes(self, obj):
        return obj.get('votes').count()

class BugReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = BugReport
        fields = ['id','title','description','screenshot','created_at']

class UpvoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Upvote
        fields = ['id','suggestion','created_at']
