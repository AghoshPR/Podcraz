from decouple import config
from django.shortcuts import render,redirect
from datetime import timedelta
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
import random,time
from email.message import EmailMessage
import smtplib
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()


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

        try:
            user_obj = User.objects.get(email=mail)
            name = user_obj.first_name or "User"
        except User.DoesNotExist:
            name = "User"

        msg = EmailMessage()
        msg['Subject'] = 'Podcraze - Password Reset OTP'
        msg['From'] = config('EMAIL_HOST_USER')
        msg['To'] = mail
        msg.set_content(
            f'Hello {name},\n\n'
            f'We received a request to reset the password for your Podcraze account.\n\n'
            f'Your OTP for password reset is: {otp}\n\n'
            f'If you did not request a password reset, please ignore this email or contact support if you have concerns. '
            f'This code will expire in 1 minute. Do not share this OTP with anyone.\n\n'
            f'Best regards,\n'
            f'The Podcraze Team'
        )
        
        server.send_message(msg)

        server.quit()
        
        return redirect('verify_otp')
    return render(request, 'user/forgot_password.html')

def otp_verify(request):
    time_otp=request.session.get('forgotpass_otp_time')
    otp_time_parsed=parse_datetime(time_otp) if time_otp else None

    if otp_time_parsed:
        elapsed=(now() - otp_time_parsed).seconds
        remaining_time=max(60 - elapsed,0)
    else:
        remaining_time=0

    if request.POST:
        action=request.POST.get('action')
        entered_otp = request.POST.get('mail-otp')
        original_otp= request.session.get('forgotpass_otp')

        if not otp_time_parsed or remaining_time <= 0:
            if action=='resend':
                new_otp = ''.join(str(random.randint(0,9)) for _ in range(4))
                request.session['forgotpass_otp'] = new_otp
                request.session['forgotpass_otp_time'] = str(now())


                #new otp sending

                mail = request.session.get('forgotpass_otpmail')
                server = smtplib.SMTP(config('EMAIL_HOST'), config('EMAIL_PORT', cast=int))
                server.starttls()
                server.login(config('EMAIL_HOST_USER'), config('EMAIL_HOST_PASSWORD'))

                try:
                    user_obj = User.objects.get(email=mail)
                    name = user_obj.first_name or "User"
                except User.DoesNotExist:
                    name = "User"

                msg = EmailMessage()
                msg['Subject'] = 'Podcraze - New Password Reset OTP'
                msg['From'] = config('EMAIL_HOST_USER')
                msg['To'] = mail
                msg.set_content(
                    f'Hello {name},\n\n'
                    f'You have requested a new OTP to reset the password for your Podcraze account.\n\n'
                    f'Your new OTP is: {new_otp}\n\n'
                    f'If you did not request a password reset, please ignore this email. '
                    f'This code will expire in 1 minute. Do not share this OTP with anyone.\n\n'
                    f'Best regards,\n'
                    f'The Podcraze Team'
                )

                server.send_message(msg)
                server.quit()

                messages.success(request, 'A new OTP has been sent to your email.')
                return redirect('verify_otp')
            
            else:
                messages.error(request, 'OTP has expired. Please request a new OTP.')
                return render(request, 'user/otp-verify.html', {'remaining_time': 0})
            


        if not entered_otp:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'user/otp-verify.html', {'remaining_time': remaining_time})

        if not entered_otp.isdigit():
            messages.error(request, 'OTP must contain only numbers.')
            return render(request, 'user/otp-verify.html', {'remaining_time': remaining_time})
        
        if len(entered_otp) != 4:
            messages.error(request, 'OTP must be exactly 4 digits.')
            return render(request, 'user/otp-verify.html', {'remaining_time': remaining_time})

        if entered_otp == original_otp:
            return redirect('reset_password')
        else:
            messages.error(request,'Invalid OTP. Please try again')
            return render(request, 'user/otp-verify.html', {'remaining_time': remaining_time})

    return render(request,'user/otp-verify.html',{'remaining_time': remaining_time})


def signup_otp(request):
    return render(request,'user/otp-sign-up.html')


