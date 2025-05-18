import os
from datetime import datetime
from pprint import pprint
import tempfile
from typing import List, Optional
from jinja2 import Template as Jinja2Templates
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import pdfkit

from api.utils.loggers import create_logger
from api.utils.settings import settings
from config import config


logger = create_logger(__name__, log_file='logs/email.log')


def generate_pdf_from_html(html: str):
    
    try:
        logger.info("Generating PDF from HTML...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            pdfkit.from_string(html, tmp_pdf.name)
            pdf_path = tmp_pdf.name
            logger.info(f"PDF generated at {pdf_path}")
            
            return pdf_path
            
    except Exception as pdf_error:
        logger.error(f"Failed to generate PDF: {pdf_error}")
        raise


def get_html_from_template(template_name: str):
    
    try:
        logger.info(f"Extracting HTML from template file {template_name}")
        
        file_path = f"{os.path.join("templates/email")}/{template_name}"
        
        with open(file_path, 'r') as html_file:
            html = html_file.read()
        
        return html
            
    except Exception as error:
        logger.error(f"Failed to extract HTML: {error}")
        raise
    

async def send_email(
    recipients: List[str], 
    subject: str, 
    template_name: Optional[str]=None, 
    html_template_string: Optional[str]=None, 
    attachments: Optional[List[str]]=None,
    template_data: Optional[dict] = {},
    apply_default_template_data: bool = True,
    add_pdf_attachment: bool = False
):
    # from premailer import transform

    logger.info('Preparing to send email')
    
    if html_template_string and template_name:
        raise ValueError("Cannot send both HTML and template-based emails. Choose one.")
    
    if not html_template_string and not template_name:
        raise ValueError("Both HTML and template name cannot be None")
    
    # logger.info(f"MAIL_USERNAME: {config('MAIL_USERNAME')}")
    # logger.info(f"MAIL_PASSWORD: {config('MAIL_PASSWORD')}")
    # logger.info(f"MAIL_FROM: {config('MAIL_FROM')}")
    # logger.info(f"MAIL_PORT: {config('MAIL_PORT')} (type: {type(config('MAIL_PORT'))})")
    # logger.info(f"MAIL_SERVER: {config('MAIL_SERVER')}")
    # logger.info(f"MAIL_FROM_NAME: {config('MAIL_FROM_NAME')}")
    # logger.info(f"TEMPLATE_FOLDER: {config('TEMPLATE_FOLDER')}")
    
    try:
        conf = ConnectionConfig(
            MAIL_USERNAME=config('MAIL_USERNAME'),
            MAIL_PASSWORD=config('MAIL_PASSWORD'),
            MAIL_FROM=config('MAIL_FROM'),
            MAIL_PORT=int(config('MAIL_PORT')),
            MAIL_SERVER=config('MAIL_SERVER'),
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            MAIL_FROM_NAME=config('MAIL_FROM_NAME'),
            TEMPLATE_FOLDER=os.path.join("templates/email") if template_name else None,
        )
        logger.info('Config set up')
        
        template_context = {
            'app_url': config('APP_URL'),
            'app_name': config('APP_NAME'),
            'company_name': 'Wren HQ',
            'terms_url': config('TERMS_URL'),
            'privacy_policy_url': config('PRIVACY_POLICY_URL'),
            'year': datetime.now().year,
            'support_email': 'josephkorede36@gmail.com',
            'help_center_url': '#',
            **template_data
        } if apply_default_template_data else template_data
        
        logger.info('Template context built')
        logger.info(template_context)
        # pprint(template_context)
        
        if template_name:
            html = get_html_from_template(template_name)
        
        if html_template_string:
            html = html_template_string
        
        jinja_template = Jinja2Templates(html)
        rendered_html = jinja_template.render(template_context)
            
        if add_pdf_attachment:
            pdf_path = generate_pdf_from_html(rendered_html)
            attachments = attachments or []
            attachments.append(pdf_path)
        
        if attachments:
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=rendered_html,
                subtype=MessageType.html,
                attachments=attachments,
            )
        else:
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=rendered_html,
                subtype=MessageType.html
            )
            
        logger.info('Message schema set up')
        
        fm = FastMail(conf)
        
        logger.info(f'Sending mail')
        await fm.send_message(message)
        
        logger.info(f"Email sent to {','.join(recipients)}")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise
