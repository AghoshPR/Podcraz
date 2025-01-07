from decouple import config
from django.shortcuts import render,redirect
from datetime import timedelta
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
import random,time
from email.message import EmailMessage
import smtplib
from django.contrib import messages


#forgot password otp
def send_otp(request):
    if request.POST:
        mail = request.POST.get('forgotpass_email')

        otp = ''.join(str(random.randint(0,9)) for _ in range(4))
        time_otp= str(now())
        
        request.session['forgotpass_otpmail'] = mail
        request.session['forgotpass_otp'] = otp
        request.session['forgotpass_otp_time'] = time_otp

        server = smtplib.SMTP(
            config('EMAIL_HOST'),
            config('EMAIL_PORT', cast=int)
        )
        server.starttls()
        server.login(
            config('EMAIL_HOST_USER'),
            config('EMAIL_HOST_PASSWORD')
        )

        msg = EmailMessage()
        msg['Subject'] = 'OTP Verification'
        msg['From'] = config('EMAIL_HOST_USER')
        msg['To'] = mail
        msg.set_content(f'Your OTP is: {otp}')
        
        server.send_message(msg)

        server.quit()
        
        return redirect('verify_otp')
    return render(request, 'user/forgot_password.html')

def otp_verify(request):

    if request.POST:
        action=request.POST.get('action')
        entered_otp = request.POST.get('mail-otp')
        original_otp= request.session.get('forgotpass_otp')
        time_otp=request.session.get('forgotpass_otp_time')

        otp_time_parsed=parse_datetime(time_otp)

        if not otp_time_parsed or now() > otp_time_parsed + timedelta(minutes=1):
            if action=='resend':
                new_otp = ''.join(str(random.randint(0,9)) for _ in range(4))
                request.session['forgotpass_otp'] = new_otp
                request.session['forgotpass_otp_time'] = str(now())


                #new otp sending

                mail = request.session.get('forgotpass_otpmail')
                server = smtplib.SMTP(config('EMAIL_HOST'), config('EMAIL_PORT', cast=int))
                server.starttls()
                server.login(config('EMAIL_HOST_USER'), config('EMAIL_HOST_PASSWORD'))

                msg = EmailMessage()
                msg['Subject'] = 'Forgot Password OTP Verification'
                msg['From'] = config('EMAIL_HOST_USER')
                msg['To'] = mail
                msg.set_content(f'Your new OTP is: {new_otp}')

                server.send_message(msg)
                server.quit()

                messages.success(request, 'A new OTP has been sent to your email.')
                return redirect('verify_otp')
            
            else:
                messages.error(request, 'OTP has expired. Please request a new OTP.')
                return render(request, 'user/otp-verify.html', {'remaining_time': 0})


        if entered_otp == original_otp:
            return redirect('reset_password')
        else:
            messages.error(request,'Invalid OTP. Please try again')
    
    time_otp=request.session.get('forgotpass_otp_time')
    otp_time_parsed=parse_datetime(time_otp)

    if otp_time_parsed:
        elapsed=(now() - otp_time_parsed).seconds
        remaining_time=max(60 - elapsed,0)
    else:
        remaining_time=0

    return render(request,'user/otp-verify.html',{'remaining_time': remaining_time})


def signup_otp(request):
    return render(request,'user/otp-sign-up.html')


