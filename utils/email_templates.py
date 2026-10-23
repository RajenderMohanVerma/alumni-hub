"""
utils/email_templates.py
========================
Centralized, ultra-modern, responsive HTML email builders for Alumni Hub.
Follows modern email client design principles (table wrappers, inline styling,
mobile-responsive viewports, high contrast typography, and accessible layouts).
"""

from typing import Optional
from markupsafe import escape


def _email_wrapper(content_html: str, preview_text: str = "Alumni Hub Notification") -> str:
    """Wraps any email body in a responsive, cross-client HTML template."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Alumni Hub</title>
    <!--[if mso]>
    <style type="text/css">
        table {{ border-collapse: collapse; }}
        body, table, td, p, a, h1, h2, h3 {{ font-family: Arial, sans-serif !important; }}
    </style>
    <![endif]-->
    <style type="text/css">
        /* Client-specific Resets */
        body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
        table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
        img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
        body {{ margin: 0; padding: 0; width: 100% !important; min-width: 100%; background-color: #f1f5f9; }}

        /* Mobile Responsive */
        @media only screen and (max-width: 600px) {{
            .email-container {{
                width: 100% !important;
                border-radius: 12px !important;
            }}
            .email-header {{
                padding: 24px 18px !important;
            }}
            .email-body {{
                padding: 24px 18px !important;
            }}
            .email-footer {{
                padding: 20px 18px !important;
            }}
            .otp-code {{
                font-size: 32px !important;
                letter-spacing: 6px !important;
            }}
            .responsive-stack {{
                display: block !important;
                width: 100% !important;
            }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #1e293b;">
    <!-- Hidden Preview Text -->
    <div style="display: none; font-size: 1px; color: #f1f5f9; line-height: 1px; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">
        {escape(preview_text)} &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;
    </div>

    <!-- Outer Table -->
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f1f5f9; table-layout: fixed;">
        <tr>
            <td align="center" style="padding: 24px 12px 36px 12px;">
                <!-- Main Email Card -->
                <table class="email-container" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08); border: 1px solid #e2e8f0;">
                    
                    <!-- Branded Header -->
                    <tr>
                        <td class="email-header" style="background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 100%); padding: 32px 30px; text-align: center;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <div style="display: inline-block; background: rgba(255, 255, 255, 0.18); border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 14px; padding: 10px 14px; margin-bottom: 12px;">
                                            <span style="font-size: 26px; line-height: 1;">🎓</span>
                                        </div>
                                        <h1 style="color: #ffffff; margin: 0 0 6px 0; font-size: 24px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase;">ALUMNI HUB</h1>
                                        <p style="color: #bae6fd; margin: 0; font-size: 13px; font-weight: 500; letter-spacing: 0.5px;">Official University Community &amp; Career Network</p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Body Content -->
                    <tr>
                        <td class="email-body" style="padding: 36px 32px 28px 32px; background-color: #ffffff;">
                            {content_html}
                        </td>
                    </tr>

                    <!-- Branded Footer -->
                    <tr>
                        <td class="email-footer" style="background-color: #f8fafc; padding: 26px 30px; border-top: 1px solid #e2e8f0; text-align: center;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center">
                                        <p style="margin: 0 0 8px 0; color: #475569; font-size: 13px; font-weight: 600;">
                                            Alumni Hub • JIMS Rohini Sector-5 Campus
                                        </p>
                                        <p style="margin: 0 0 14px 0; color: #94a3b8; font-size: 12px; line-height: 1.5;">
                                            Building lifelong connections between students, distinguished alumni, and faculty.
                                        </p>
                                        <div style="margin: 0 0 14px 0;">
                                            <span style="display: inline-block; background-color: #e2e8f0; height: 1px; width: 60px;"></span>
                                        </div>
                                        <p style="margin: 0; color: #94a3b8; font-size: 11px;">
                                            &copy; 2026 Alumni Hub. All rights reserved.<br>
                                            This is an automated system notification. Please do not reply directly unless specified.
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def build_otp_email(otp: str, purpose: str = "registration", expires_in_minutes: int = 2, user_name: Optional[str] = None) -> str:
    """
    Builds a stunning, responsive OTP verification email.
    purpose: 'registration' | 'registration_resend' | 'password_reset'
    """
    greeting = f"Hi <strong>{escape(user_name)}</strong>," if user_name else "Hello,"

    if purpose == "password_reset":
        badge_text = "🔐 Password Reset Request"
        badge_bg = "#fef2f2"
        badge_color = "#dc2626"
        heading = "Reset Your Password"
        message_intro = f"{greeting}<br>We received a request to reset the password for your Alumni Hub account. Use the secure One-Time Password (OTP) below to proceed with setting your new password."
        preview_text = f"Your Alumni Hub password reset OTP is {otp}"
    elif purpose == "registration_resend":
        badge_text = "⚡ New Verification Code"
        badge_bg = "#f0f9ff"
        badge_color = "#0284c7"
        heading = "Verify Your Email Address"
        message_intro = f"{greeting}<br>Here is your freshly generated verification code. Enter this code to verify your email address and activate your account."
        preview_text = f"Your new verification OTP is {otp}"
    else:
        badge_text = "🛡️ Identity Verification"
        badge_bg = "#e0f2fe"
        badge_color = "#0369a1"
        heading = "Verify Your Email Address"
        message_intro = f"{greeting}<br>Welcome to <strong>Alumni Hub</strong>! Please use the following One-Time Password (OTP) to confirm your email address and complete your registration."
        preview_text = f"Your verification OTP is {otp} for Alumni Hub"

    body_content = f"""
    <div style="text-align: center; margin-bottom: 22px;">
        <span style="display: inline-block; background-color: {badge_bg}; color: {badge_color}; border: 1px solid rgba(0,0,0,0.06); padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            {badge_text}
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 14px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        {heading}
    </h2>

    <p style="font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin: 0 0 24px 0;">
        {message_intro}
    </p>

    <!-- OTP Display Box -->
    <div style="background: linear-gradient(180deg, #f8fafc 0%, #f0f9ff 100%); border: 2px dashed #0284c7; border-radius: 16px; padding: 24px 20px; text-align: center; margin: 26px 0;">
        <div style="font-size: 12px; font-weight: 700; color: #64748b; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;">
            Your One-Time Password (OTP)
        </div>
        <div class="otp-code" style="font-family: 'Courier New', Consolas, monospace; font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #0284c7; line-height: 1.2; margin: 6px 0;">
            {escape(otp)}
        </div>
        <div style="margin-top: 10px;">
            <span style="display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 4px 14px; border-radius: 50px; font-size: 12px; font-weight: 700;">
                ⏱️ Valid for {expires_in_minutes} minutes
            </span>
        </div>
    </div>

    <!-- Security Warning Box -->
    <div style="background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 14px 16px; border-radius: 8px; margin: 24px 0;">
        <p style="margin: 0; font-size: 13px; color: #92400e; line-height: 1.5;">
            <strong>🔒 Security Alert:</strong> Never share this code with anyone. Alumni Hub staff will never call, text, or email you asking for your verification code.
        </p>
    </div>

    <p style="font-size: 13px; color: #94a3b8; text-align: center; line-height: 1.5; margin: 20px 0 0 0;">
        If you did not initiate this request, you can safely ignore this email. Your account remains completely secure.
    </p>
    """
    return _email_wrapper(body_content, preview_text=preview_text)


def build_contact_user_confirmation_email(name: str, email: str, subject: str, message: str, submission_time: str) -> str:
    """Builds a polished confirmation email sent to the user who submitted the contact form."""
    preview_text = f"We have received your message regarding: {subject}"
    body_content = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #dcfce7; color: #166534; padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            ✓ Message Received Successfully
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 12px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        Thank You for Reaching Out
    </h2>

    <p style="font-size: 15px; color: #475569; line-height: 1.6; margin: 0 0 20px 0;">
        Dear <strong>{escape(name)}</strong>,<br><br>
        We have safely received your inquiry through the Alumni Hub portal. Our administrative and community support team has been notified and is currently reviewing your message.
    </p>

    <!-- Details Card -->
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 20px; margin: 22px 0;">
        <h3 style="margin: 0 0 14px 0; font-size: 14px; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px;">
            📋 Your Submission Summary
        </h3>
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 1.6;">
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600; width: 30%;">Subject:</td>
                <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{escape(subject)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Submitted On:</td>
                <td style="padding: 6px 0; color: #334155;">{escape(submission_time)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Status:</td>
                <td style="padding: 6px 0;"><span style="color: #0284c7; font-weight: 700;">● Under Review</span></td>
            </tr>
        </table>

        <div style="margin-top: 14px; padding-top: 14px; border-top: 1px dashed #cbd5e1;">
            <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: 700; color: #64748b; text-transform: uppercase;">Your Message:</p>
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 14px; color: #334155; font-size: 13px; line-height: 1.5; white-space: pre-wrap;">{escape(message)}</div>
        </div>
    </div>

    <!-- What's Next Steps -->
    <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 12px; padding: 16px 18px; margin: 20px 0;">
        <h4 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 700; color: #166534;">
            ⏱️ What Happens Next?
        </h4>
        <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #15803d; line-height: 1.6;">
            <li>Our coordinators will review your note within <strong>24 to 48 business hours</strong>.</li>
            <li>We will reply directly to this email address (<strong>{escape(email)}</strong>).</li>
            <li>For urgent campus matters, you may call our reception at <strong>+91 11 45184000</strong>.</li>
        </ul>
    </div>
    """
    return _email_wrapper(body_content, preview_text=preview_text)


def build_contact_admin_alert_email(name: str, email: str, role_type: str, subject: str, message: str, submission_time: str) -> str:
    """Builds an alert email sent to the Alumni Hub admin upon receiving a new contact message."""
    preview_text = f"New Contact Message from {name}: {subject}"
    body_content = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #fef3c7; color: #92400e; padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            📨 Incoming Contact Inquiry
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 12px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        New Contact Submission
    </h2>

    <p style="font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin: 0 0 24px 0;">
        A user has submitted an inquiry through the public Alumni Hub contact form.
    </p>

    <!-- Details Card -->
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin: 20px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 1.6;">
            <tr>
                <td style="padding: 7px 0; color: #64748b; font-weight: 600; width: 32%;">Sender Name:</td>
                <td style="padding: 7px 0; color: #0f172a; font-weight: 700;">{escape(name)}</td>
            </tr>
            <tr>
                <td style="padding: 7px 0; color: #64748b; font-weight: 600;">Email:</td>
                <td style="padding: 7px 0;">
                    <a href="mailto:{escape(email)}" style="color: #0284c7; text-decoration: none; font-weight: 600;">{escape(email)}</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 7px 0; color: #64748b; font-weight: 600;">Affiliation / Role:</td>
                <td style="padding: 7px 0;">
                    <span style="display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 2px 10px; border-radius: 50px; font-size: 12px; font-weight: 700; text-transform: uppercase;">
                        {escape(role_type)}
                    </span>
                </td>
            </tr>
            <tr>
                <td style="padding: 7px 0; color: #64748b; font-weight: 600;">Subject:</td>
                <td style="padding: 7px 0; color: #0f172a; font-weight: 700;">{escape(subject)}</td>
            </tr>
            <tr>
                <td style="padding: 7px 0; color: #64748b; font-weight: 600;">Received:</td>
                <td style="padding: 7px 0; color: #64748b;">{escape(submission_time)}</td>
            </tr>
        </table>

        <!-- Message Body -->
        <div style="margin-top: 18px; padding-top: 16px; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 700; color: #0f172a;">💬 Message Content:</p>
            <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 10px; padding: 16px; font-size: 14px; line-height: 1.6; color: #334155; white-space: pre-wrap; word-break: break-word;">
                {escape(message)}
            </div>
        </div>
    </div>

    <!-- Quick Action Button -->
    <div style="text-align: center; margin: 28px 0 10px 0;">
        <a href="mailto:{escape(email)}?subject=Re:%20{escape(subject)}" style="display: inline-block; background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 50px; font-weight: 700; font-size: 14px; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);">
            ↩️ Reply to {escape(name)}
        </a>
    </div>
    """
    return _email_wrapper(body_content, preview_text=preview_text)


def build_pending_registration_admin_email(name: str, email: str, phone: str, role: str, review_url: str) -> str:
    """Builds an alert email sent to admin when a new user registers and awaits approval."""
    preview_text = f"New {role.title()} registration pending approval: {name}"
    body_content = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #fef3c7; color: #92400e; padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            ⏳ Verification Required
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 12px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        New {escape(role.title())} Registration
    </h2>

    <p style="font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin: 0 0 22px 0;">
        A new member has verified their email address and is waiting for your administrative verification to join the portal.
    </p>

    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin: 20px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 1.6;">
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600; width: 32%;">Applicant Name:</td>
                <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{escape(name)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Email Address:</td>
                <td style="padding: 6px 0; color: #0284c7; font-weight: 600;">{escape(email)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Phone Number:</td>
                <td style="padding: 6px 0; color: #334155;">{escape(phone or 'Not provided')}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Account Role:</td>
                <td style="padding: 6px 0;">
                    <span style="display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 2px 10px; border-radius: 50px; font-size: 12px; font-weight: 700; text-transform: uppercase;">
                        {escape(role)}
                    </span>
                </td>
            </tr>
        </table>
    </div>

    <div style="text-align: center; margin: 28px 0 10px 0;">
        <a href="{escape(review_url)}" style="display: inline-block; background: linear-gradient(135deg, #0284c7 0%, #1e3a8a 100%); color: #ffffff; text-decoration: none; padding: 13px 30px; border-radius: 50px; font-weight: 700; font-size: 14px; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);">
            Review &amp; Approve in Admin Portal &rarr;
        </a>
    </div>
    """
    return _email_wrapper(body_content, preview_text=preview_text)


def build_pending_job_admin_email(title: str, company: str, location: str, work_mode: str, employment_type: str, poster_name: str, poster_email: str, review_url: str) -> str:
    """Builds an alert email sent to admin when a job is posted and awaits approval."""
    preview_text = f"New Job Posted: {title} at {company}"
    body_content = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #e0e7ff; color: #4338ca; padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            💼 Career Opportunity Approval
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 12px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        New Job Pending Approval
    </h2>

    <p style="font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin: 0 0 22px 0;">
        An alumni or faculty member has posted a new career opportunity for student candidates.
    </p>

    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin: 20px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 1.6;">
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600; width: 32%;">Job Title:</td>
                <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{escape(title)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Hiring Company:</td>
                <td style="padding: 6px 0; color: #0284c7; font-weight: 700;">{escape(company)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Location &amp; Mode:</td>
                <td style="padding: 6px 0; color: #334155;">{escape(location)} ({escape(work_mode)})</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Employment:</td>
                <td style="padding: 6px 0; color: #334155;">{escape(employment_type)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Posted By:</td>
                <td style="padding: 6px 0; color: #334155;">{escape(poster_name)} ({escape(poster_email)})</td>
            </tr>
        </table>
    </div>

    <div style="text-align: center; margin: 28px 0 10px 0;">
        <a href="{escape(review_url)}" style="display: inline-block; background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%); color: #ffffff; text-decoration: none; padding: 13px 30px; border-radius: 50px; font-weight: 700; font-size: 14px; box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);">
            Review Job Posting &rarr;
        </a>
    </div>
    """
    return _email_wrapper(body_content, preview_text=preview_text)


def build_issue_report_admin_email(reporter_name: str, reporter_email: str, issue_type: str, description: str, submission_time: str) -> str:
    """Builds an alert email sent to admin when a user reports a bug or issue."""
    preview_text = f"Issue Reported: {issue_type} from {reporter_name}"
    body_content = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #fee2e2; color: #991b1b; padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            🚨 Platform Issue Reported
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 12px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        Incident / Feedback Ticket
    </h2>

    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin: 20px 0;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-size: 14px; line-height: 1.6;">
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600; width: 32%;">Category:</td>
                <td style="padding: 6px 0; color: #dc2626; font-weight: 700;">{escape(issue_type)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Reported By:</td>
                <td style="padding: 6px 0; color: #0f172a; font-weight: 700;">{escape(reporter_name)}</td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Email:</td>
                <td style="padding: 6px 0;">
                    <a href="mailto:{escape(reporter_email)}" style="color: #0284c7; text-decoration: none; font-weight: 600;">{escape(reporter_email)}</a>
                </td>
            </tr>
            <tr>
                <td style="padding: 6px 0; color: #64748b; font-weight: 600;">Timestamp:</td>
                <td style="padding: 6px 0; color: #64748b;">{escape(submission_time)}</td>
            </tr>
        </table>

        <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 8px 0; font-size: 13px; font-weight: 700; color: #0f172a;">Description of the Issue:</p>
            <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; font-size: 13px; line-height: 1.6; color: #334155; white-space: pre-wrap;">
                {escape(description)}
            </div>
        </div>
    </div>
    """
    return _email_wrapper(body_content, preview_text=preview_text)


def build_direct_message_email(sender_name: str, sender_role: str, sender_email: str, subject: str, message_body: str, profile_url: str, whatsapp_url: Optional[str] = None, linkedin_url: Optional[str] = None) -> str:
    """Builds a responsive direct communication email sent from one member to another."""
    preview_text = f"Message from {sender_name}: {subject}"
    body_content = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span style="display: inline-block; background-color: #e0f2fe; color: #0369a1; padding: 6px 16px; border-radius: 50px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;">
            💬 Hub Message
        </span>
    </div>

    <h2 style="color: #0f172a; text-align: center; margin: 0 0 12px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.3px;">
        {escape(subject)}
    </h2>

    <p style="font-size: 15px; color: #475569; line-height: 1.6; text-align: center; margin: 0 0 20px 0;">
        <strong>{escape(sender_name)}</strong> ({escape(sender_role.title())}) has sent you a direct message via the Alumni Hub platform.
    </p>

    <!-- Message Bubble -->
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 22px; margin: 22px 0;">
        <div style="font-size: 14px; line-height: 1.65; color: #1e293b; white-space: pre-wrap;">
            {escape(message_body)}
        </div>
    </div>

    <!-- Quick CTAs -->
    <div style="text-align: center; margin: 26px 0 10px 0;">
        <a href="{escape(profile_url)}" style="display: inline-block; background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 50px; font-weight: 700; font-size: 13px; margin: 4px;">
            👤 View Profile
        </a>
        <a href="mailto:{escape(sender_email)}?subject=Re:%20{escape(subject)}" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 50px; font-weight: 700; font-size: 13px; margin: 4px;">
            ✉️ Reply via Email
        </a>
    </div>
    """
    return _email_wrapper(body_content, preview_text=preview_text)
