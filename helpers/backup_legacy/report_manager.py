"""
Handles email reports and web dashboard exports
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import pandas as pd
from datetime import datetime
import os

class ReportManager:
    def __init__(self, smtp_config):
        self.smtp_config = smtp_config
        
    def generate_daily_summary(self, production_data):
        """Generate daily KPI summary"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Extract key metrics
        daily_metrics = {
            "Total Production": production_data["daily"].get("total", 0),
            "Quality Rate": production_data["daily"].get("quality_rate", 0),
            "Target Achievement": production_data["daily"].get("target_achievement", 0),
        }
        
        # Format email content
        html_content = f"""
        <h2>Daily Production Summary - {today}</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
        """
        
        for metric, value in daily_metrics.items():
            html_content += f"<tr><td>{metric}</td><td>{value}</td></tr>"
            
        html_content += "</table>"
        
        return html_content
        
    def send_email_report(self, recipient, subject, html_content, pdf_attachment=None):
        """Send email with optional PDF attachment"""
        msg = MIMEMultipart()
        msg["From"] = self.smtp_config["username"]
        msg["To"] = recipient
        msg["Subject"] = subject
        
        # Add HTML content
        msg.attach(MIMEText(html_content, "html"))
        
        # Add PDF if provided
        if pdf_attachment:
            with open(pdf_attachment, "rb") as f:
                pdf = MIMEApplication(f.read(), _subtype="pdf")
                pdf.add_header('Content-Disposition', 'attachment', filename=os.path.basename(pdf_attachment))
                msg.attach(pdf)
        
        # Send email
        with smtplib.SMTP(self.smtp_config["server"], self.smtp_config["port"]) as server:
            server.starttls()
            server.login(self.smtp_config["username"], self.smtp_config["password"])
            server.send_message(msg)
            
    def schedule_reports(self):
        """Schedule automated reports"""
        # Daily report at 6 PM
        # Weekly report on Friday
        # Monthly report on last day
        pass
    
    def export_to_pdf(self, production_data):
        """Export dashboard as PDF"""
        # TODO: Implement PDF export
        pass
    
    def prepare_web_dashboard_data(self, production_data):
        """Prepare data for web dashboard"""
        # Format data for web consumption
        dashboard_data = {
            "daily": production_data["daily"],
            "weekly": production_data["weekly"],
            "monthly": production_data["monthly"],
            "last_updated": datetime.now().isoformat()
        }
        return dashboard_data
