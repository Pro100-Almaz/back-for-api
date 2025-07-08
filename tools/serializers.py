from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tool, ToolUsage, ToolFeedback, ToolApiKey

User = get_user_model()


class ToolSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    creator_email = serializers.CharField(source='creator.email', read_only=True)
    
    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'description', 'category', 'status', 'creator',
            'creator_name', 'creator_email', 'points_cost', 'api_endpoint',
            'api_documentation', 'tags', 'version', 'total_uses', 'total_revenue',
            'average_rating', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'creator', 'total_uses', 'total_revenue', 'average_rating',
            'created_at', 'updated_at'
        ]


class ToolListSerializer(serializers.ModelSerializer):
    """Serializer for listing tools with basic info"""
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    
    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'description', 'category', 'status', 'creator_name',
            'points_cost', 'total_uses', 'average_rating', 'created_at'
        ]


class ToolCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tools"""
    
    class Meta:
        model = Tool
        fields = [
            'name', 'description', 'category', 'points_cost', 'api_endpoint',
            'api_documentation', 'tags', 'version'
        ]
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class ToolUsageSerializer(serializers.ModelSerializer):
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = ToolUsage
        fields = [
            'id', 'tool', 'tool_name', 'user', 'user_email', 'input_data',
            'output_data', 'points_spent', 'execution_time', 'success',
            'error_message', 'created_at'
        ]
        read_only_fields = [
            'id', 'user', 'points_spent', 'execution_time', 'success',
            'error_message', 'created_at'
        ]


class ToolUsageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tool usage records"""
    
    class Meta:
        model = ToolUsage
        fields = ['tool', 'input_data']
    
    def validate(self, attrs):
        user = self.context['request'].user
        tool = attrs['tool']
        
        # Check if tool can be used
        if not tool.can_be_used_by(user):
            raise serializers.ValidationError("Cannot use this tool")
        
        # Check if user has enough points
        if user.is_client and user.points_balance < tool.points_cost:
            raise serializers.ValidationError("Insufficient points")
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        tool = validated_data['tool']
        
        # Create usage record
        usage = ToolUsage.objects.create(
            tool=tool,
            user=user,
            input_data=validated_data.get('input_data'),
            points_spent=tool.points_cost
        )
        
        # Deduct points from user
        if user.is_client:
            user.points_balance -= tool.points_cost
            user.save()
        
        # Update tool statistics
        tool.total_uses += 1
        tool.save()
        
        return usage


class ToolFeedbackSerializer(serializers.ModelSerializer):
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ToolFeedback
        fields = [
            'id', 'tool', 'tool_name', 'user', 'user_name', 'rating',
            'comment', 'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        user = self.context['request'].user
        tool = attrs['tool']
        
        # Check if user has used this tool
        if not ToolUsage.objects.filter(user=user, tool=tool).exists():
            raise serializers.ValidationError("You must use the tool before providing feedback")
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        feedback = super().create(validated_data)
        
        # Update tool's average rating
        tool = feedback.tool
        ratings = ToolFeedback.objects.filter(tool=tool)
        avg_rating = sum(f.rating for f in ratings) / ratings.count()
        tool.average_rating = round(avg_rating, 2)
        tool.save()
        
        return feedback


class ToolApiKeySerializer(serializers.ModelSerializer):
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    
    class Meta:
        model = ToolApiKey
        fields = [
            'id', 'tool', 'tool_name', 'key_name', 'api_key', 'is_active',
            'daily_limit', 'monthly_limit', 'daily_usage', 'monthly_usage',
            'created_at', 'last_used'
        ]
        read_only_fields = [
            'id', 'api_key', 'daily_usage', 'monthly_usage', 'created_at', 'last_used'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        
        # Generate API key (in production, use a proper key generation method)
        import secrets
        validated_data['api_key'] = f"tk_{secrets.token_urlsafe(32)}"
        
        return super().create(validated_data)


class ToolUsageStatsSerializer(serializers.Serializer):
    """Serializer for tool usage statistics"""
    total_uses = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    recent_usage = serializers.ListField(child=serializers.DictField()) 