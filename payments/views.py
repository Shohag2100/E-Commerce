import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Payment
from .serializers import PaymentSerializer
from orders.models import Order

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def create_payment_intent(self, request):
        """Create a Stripe payment intent for an order"""
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response(
                {'error': 'Order ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if order.paid:
            return Response(
                {'error': 'Order already paid'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if payment already exists
        if hasattr(order, 'payment'):
            payment = order.payment
            if payment.status == 'succeeded':
                return Response(
                    {'error': 'Order already paid'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Create Stripe PaymentIntent
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'order_id': order.id,
                    'order_number': order.order_number
                },
                description=f'Payment for Order {order.order_number}'
            )
            
            # Save or update payment record
            payment, created = Payment.objects.update_or_create(
                order=order,
                defaults={
                    'stripe_payment_intent_id': intent.id,
                    'amount': order.total_amount,
                    'currency': 'usd',
                    'status': 'pending'
                }
            )
            
            order.stripe_payment_intent = intent.id
            order.save()
            
            return Response({
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'payment_id': payment.id,
                'amount': order.total_amount,
                'publishable_key': settings.STRIPE_PUBLIC_KEY
            })
            
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def confirm_payment(self, request):
        """Confirm payment status"""
        payment_intent_id = request.data.get('payment_intent_id')
        
        if not payment_intent_id:
            return Response(
                {'error': 'Payment intent ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Retrieve payment intent from Stripe
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Update payment and order status
            try:
                payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
            except Payment.DoesNotExist:
                return Response(
                    {'error': 'Payment not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            payment.status = intent.status
            
            if intent.status == 'succeeded':
                payment.stripe_payment_method = intent.payment_method
                payment.save()
                
                order = payment.order
                order.paid = True
                order.paid_at = timezone.now()
                order.status = 'processing'
                order.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Payment successful',
                    'order_id': order.id,
                    'order_number': order.order_number
                })
            
            elif intent.status == 'requires_payment_method':
                payment.status = 'failed'
                payment.error_message = 'Payment method failed'
                payment.save()
                return Response({
                    'status': 'failed',
                    'message': 'Payment failed. Please try another payment method.'
                })
            
            else:
                payment.save()
                return Response({
                    'status': intent.status,
                    'message': f'Payment status: {intent.status}'
                })
                
        except stripe.error.StripeError as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'An error occurred: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_payments(self, request):
        """Get user's payment history"""
        payments = Payment.objects.filter(order__user=request.user)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse('Webhook secret not configured', status=400)
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse('Invalid payload', status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse('Invalid signature', status=400)
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'succeeded'
            payment.stripe_payment_method = payment_intent.get('payment_method', '')
            payment.save()
            
            order = payment.order
            order.paid = True
            order.paid_at = timezone.now()
            order.status = 'processing'
            order.save()
            
        except Payment.DoesNotExist:
            pass
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'failed'
            payment.error_message = payment_intent.get('last_payment_error', {}).get('message', '')
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    elif event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            payment.status = 'cancelled'
            payment.save()
        except Payment.DoesNotExist:
            pass
    
    return HttpResponse(status=200)