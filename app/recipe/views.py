from rest_framework import viewsets, mixins
from recipe.serializers import (
    RecipeSerializer, RecipeDetailSerializer,
    TagSerializer, IngredientSerializer)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe, Tag, Ingredient


class RecipesViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs"""
    serializer_class = RecipeDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Recipe.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        if self.action == 'list':
            return RecipeSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TagViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    """Manage tags in database"""
    serializer_class = TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Tag.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')


class IngredientViewSet(mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                        mixins.ListModelMixin, viewsets.GenericViewSet):
    """Manage ingredient in database"""
    serializer_class = IngredientSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Ingredient.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')
