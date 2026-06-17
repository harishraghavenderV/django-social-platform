import qrcode
import io
import base64
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_otp import login as otp_login, user_has_device
from django_otp.plugins.otp_totp.models import TOTPDevice

def get_qr_data_uri(config_url):
    qr = qrcode.QRCode(version=1, box_size=6, border=4)
    qr.add_data(config_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

@login_required
def setup_2fa(request):
    # Check if user already has a confirmed 2FA device
    confirmed_device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
    if confirmed_device:
        return render(request, "users/2fa_setup.html", {"already_enabled": True})
        
    # Get or create an unconfirmed device
    device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
    if not device:
        device = TOTPDevice.objects.create(user=request.user, name="default", confirmed=False)
        
    if request.method == "POST":
        token = request.POST.get("token")
        if token and device.verify_token(token):
            device.confirmed = True
            device.save()
            # Clean up other unconfirmed devices if any
            TOTPDevice.objects.filter(user=request.user, confirmed=False).exclude(id=device.id).delete()
            otp_login(request, device)
            return JsonResponse({'success': True, 'message': 'Two-Factor Authentication setup successful!'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid code. Please try again.'})
            
    qr_uri = get_qr_data_uri(device.config_url)
    return render(request, "users/2fa_setup.html", {
        "qr_uri": qr_uri,
        "device": device,
        "already_enabled": False
    })

@login_required
@require_POST
def disable_2fa(request):
    TOTPDevice.objects.filter(user=request.user).delete()
    return JsonResponse({'success': True, 'message': 'Two-Factor Authentication disabled successfully.'})

def verify_2fa(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    # If the user has no device or is already verified, redirect home
    if not user_has_device(request.user) or request.user.is_verified():
        return redirect('home')
        
    if request.method == "POST":
        token = request.POST.get("token")
        device = TOTPDevice.objects.filter(user=request.user, confirmed=True).first()
        if device and token and device.verify_token(token):
            otp_login(request, device)
            return JsonResponse({'success': True, 'message': 'Verification successful!'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid code. Please try again.'})
            
    return render(request, "users/2fa_verify.html")
