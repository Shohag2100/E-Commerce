from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderCreateSerializer
from products.models import Cart

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        elif user.is_authenticated:
            return Order.objects.filter(user=user)
        return Order.objects.none()
    
    def create(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Get cart
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_id = request.session.session_key
            if not session_id:
                return Response({'error': 'No session found'}, status=status.HTTP_400_BAD_REQUEST)
            cart = Cart.objects.filter(session_id=session_id).first()
        
        if not cart or not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check stock availability
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                return Response({
                    'error': f'Insufficient stock for {item.product.name}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order
        order = serializer.save(
            user=request.user if request.user.is_authenticated else None,
            total_amount=cart.total
        )
        
        # Create order items and update stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_price=item.product.price,
                quantity=item.quantity
            )
            
            # Update product stock
            item.product.stock -= item.quantity
            item.product.save()
        
        # Clear cart
        cart.items.all().delete()
        
        return Response(
            OrderSerializer(order).data, 
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_orders(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
