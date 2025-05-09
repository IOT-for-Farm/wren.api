from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import and_, or_, desc, asc
from sqlalchemy.orm import Session
from slugify import slugify
from secrets import token_hex
from config import config
from jose import JWTError, jwt

from api.core.dependencies.email_sending_service import send_email
from api.utils.helpers import generate_unique_id
from api.utils.loggers import create_logger
from api.utils.settings import settings
from api.v1.models.organization import Organization, OrganizationRole, OrganizationMember, OrganizationInvite
from api.v1.models.location import Location
from api.v1.models.contact_info import ContactInfo
from api.v1.models.token import TokenType
from api.v1.models.user import User
from api.v1.schemas import organization as organization_schemas
from api.v1.schemas import contact_info as contact_info_schemas
from api.v1.schemas.auth import CreateUser
from api.v1.services.token import TokenService
from api.v1.services.user import UserService


logger = create_logger(__name__)

class OrganizationService:
    
    @classmethod
    def role_exists_in_org(cls, db: Session, organization_id: str, role_id: str):
        '''Function to check if a role exists in the organization'''
        
        # Check if organization exists
        organization = Organization.fetch_by_id(db, organization_id)
        
        # Check if role id exists in the organization or in the default organization
        role_exists = db.query(OrganizationRole).filter(
            or_(
                OrganizationRole.organization_id == '-1',
                OrganizationRole.organization_id == organization.id,
            )
        ).filter(OrganizationRole.id == role_id, OrganizationRole.is_deleted==False).first()
        
        if not role_exists:
            raise HTTPException(400, 'Selected role does not exist in this organization')
        
        return True
    
    
    @classmethod
    def user_exists_in_org(cls, db: Session, organization_id: str, user_id: str):
        '''Function to check if a user exists in the organization'''
        
        # Check if organization exists
        organization = Organization.fetch_by_id(db, organization_id)
        
        # Check if user exists
        user = User.fetch_by_id(db, user_id)
        
        if user.is_superuser:
            return True
        
        # Check if user exists in the organization
        user_exists = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization.id,
            OrganizationMember.user_id == user.id,
            OrganizationMember.is_deleted == False
        ).first()
        
        if not user_exists:
            raise HTTPException(400, 'User does not exist in this organization')
        
        return True
    
    @classmethod
    def create(cls, db: Session, user_id: str, payload: organization_schemas.CreateOrganization):
        '''Function to create an organization'''
        
        if not payload.slug:
            slug = slugify(payload.name)
            
            # Check for any organization with the same slug
            existing_org_with_slug = Organization.fetch_one_by_field(
                db=db, throw_error=False, slug=slug
            )
            
            if existing_org_with_slug:
                # Append unique string to organization name to make the url slug unique
                slug = slugify(f'{payload.name}-{token_hex(5)}')
            
            payload.slug = slug
            logger.info('Slug generated')
        
        # generate unique id
        payload.unique_id = (
            generate_unique_id(name=payload.name) 
            if not payload.unique_id 
            else payload.unique_id
        )
        
        payload.logo_url=f'https://ui-avatars.com/api/?name={payload.name}' if not payload.logo_url else payload.logo_url
        
        # Create location
        organization = Organization.create(
            db=db,
            created_by=user_id,
            **payload.model_dump(
                exclude_unset=True,
                exclude=[
                    'email', 'phone', 'phone_country_code', 
                    'state', 'city', 'country', 'address', 'postal_code'
                ]
            )
        )
        logger.info(f'New organization {organization .name} created')
        
        # Create email contact info
        if payload.email:
            ContactInfo.create(
                db=db,
                model_name='organizations',
                model_id=organization.id,
                contact_type=contact_info_schemas.ContactType.EMAIL.value,
                contact_data=payload.email,
                is_primary=True
            )
            logger.info('Email contact info added for organization')
        
        # Create phone number contact info
        if payload.phone and payload.phone_country_code:
            ContactInfo.create(
                db=db,
                model_name='organizations',
                model_id=organization.id,
                contact_type=contact_info_schemas.ContactType.PHONE.value,
                contact_data=payload.phone,
                phone_country_code=payload.phone_country_code,
                is_primary=True
            )
            logger.info('Phone contact info added for organization')
            
        # Create organization location
        Location.create(
            db=db,
            model_name='organizations',
            model_id=organization.id,
            # address=payload.address,
            **payload.model_dump(
                exclude_unset=True,
                include=['state', 'city', 'country', 'address', 'postal_code']
            )
        )
        logger.info('Location added for organization')
        
        # Get owner role
        role = OrganizationRole.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id='-1',
            role_name='Owner'
        )
        
        # Add user to organization members with the role of owner
        OrganizationMember.create(
            db=db,
            organization_id=organization.id,
            user_id=user_id,
            role_id=role.id,
            is_primary_contact=True
        )
        logger.info('User added to organization as an owner')
        
        return organization
    
    
    @classmethod
    def get_user_organizations(cls, db: Session, user_id: str, name: Optional[str] = None):
        '''Function to get a users organizations'''
        
        query = (
            db.query(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .join(User, User.id == OrganizationMember.user_id)
            .filter(
                and_(
                    User.id == user_id, 
                    Organization.is_deleted == False, 
                    OrganizationMember.is_active == True,
                    OrganizationMember.is_deleted == False
                )
            )
        )
        
        if name:
            name_search = f"%{name}%"
            query = query.filter(Organization.name.ilike(name_search))
        
        query = query.order_by(OrganizationMember.join_date.desc())
        
        organizations = query.all()
        
        return organizations

    
    @classmethod
    def get_organization_members(
        cls, 
        db: Session, 
        organization_id: str, 
        page: int = 1,
        per_page: int = 10,
        sort_by: str = 'join_date',
        order: str = 'desc',
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        paginate: bool = True
    ):
        '''Function to get organization members'''
        
        query = (
            db.query(OrganizationMember)
            .join(User, OrganizationMember.user_id == User.id)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.is_deleted == False
            )
        )
        
        if full_name:
            names = full_name.split(' ')
            if len(names) > 1:
                first_name, last_name = f'%{names[0]}%', f'%{names[-1]}%'
            else:
                first_name, last_name = f'%{names[0]}%', None
            
            query = query.filter(User.first_name.ilike(first_name))
            
            if last_name:
                query = query.filter(User.last_name.ilike(last_name))
        
        if email:
            query = query.filter(User.email.ilike(f'%{email}%'))
        
        # query = query.order_by(OrganizationMember.join_date.desc())
        if order == "desc":
            query = query.order_by(desc(getattr(OrganizationMember, sort_by)))
        else:
            query = query.order_by(getattr(OrganizationMember, sort_by))
        
        # members = query.all()
        
        # return members
        
        count = query.count()

        # Handle pagination
        if paginate:
            offset = (page - 1) * per_page
            return query.offset(offset).limit(per_page).all(), count
        else:
            return query.all(), count
    
    
    @classmethod
    def invite_user(
        cls, 
        db: Session, 
        bg_tasks: BackgroundTasks,
        payload: organization_schemas.InviteUser,
        inviter_id: str,
        organization_id: str
    ):
        '''Fucntion to send an invite to an organization to a usuer'''
        
        # Get organization
        organization = Organization.fetch_by_id(db, organization_id)
        
        # Check if role exists
        cls.role_exists_in_org(db, organization.id, payload.role_id)
        
        # Check if user exists in organization through email
        org_members, count = cls.get_organization_members(db, organization.id, paginate=False)
        org_members_emails = [member.user.email for member in org_members]
        logger.info(f'Current org members: {org_members_emails}')
        
        if payload.email in org_members_emails:
            raise HTTPException(400, 'User already belongs to organization')
        
        # Check if there is a pending invite already for the user
        pending_invite_for_user = OrganizationInvite.fetch_one_by_field(
            db=db, throw_error=False,
            organization_id=organization.id,
            email=payload.email,
            status='pending'
        )
        
        if pending_invite_for_user:
            # Delete the pending invite and resend a new one
            pending_invite_for_user.is_deleted = True
            db.commit()
            # raise HTTPException(400, 'There is already a pending invite for this user')
        
        # Generate invite token
        expiry_minutes = 60
        invite_token = TokenService.create_token(
            db=db,
            token_type=TokenType.ORG_INVITE.value,
            expiry_in_minutes=expiry_minutes,
            payload={"email": payload.email, "organization_id": organization.id},
            user_id=inviter_id
        )
        
        invite = OrganizationInvite.create(
            db=db,
            organization_id=organization_id,
            invite_token=invite_token,
            inviter_id=inviter_id,
            **payload.model_dump()
        )
        
        # Send email to user
        # TODO: Update the url
        bg_tasks.add_task(
            send_email,
            recipients=[payload.email],
            template_name='organization-invite.html',
            subject=f'You have been invited to {organization.name} on {config("APP_NAME")}',
            template_data={
                'recipient_email': payload.email,
                'invite_url': f"{config('APP_URL')}/organizations/invites/respond",
                'token': invite_token,
                'expiry_minutes': expiry_minutes,
                'invite': invite,
                'organization': organization
            }
        )
        
        return invite
        
    @classmethod
    def update_invitation(
        cls, 
        db: Session, 
        status: str,
        bg_tasks: BackgroundTasks,
        token: Optional[str]=None, 
        invite_id: Optional[str]=None,
    ):
        '''Function to basically update an invite.
        If the invite is accepted then the user will be added to the organization and if not, the status will be updated
        '''
        
        credentials_exception = HTTPException(401, 'Could not verify token')
        
        if not token and not invite_id:
            raise HTTPException(400, 'Either an invite token or invite id is needed')
        
        if status == 'pending':
            raise HTTPException(400, 'Cannot update invitation status to pending')
        
        logger.info('Fetching invitation record')
        invite = None
        invite_dict = {}
        if token:
            invite_token = token
            invite = OrganizationInvite.fetch_one_by_field(db, invite_token=token)
            # invite_dict = invite.to_dict()
        
        if invite_id:
            invite = OrganizationInvite.fetch_by_id(db, invite_id)
            invite_token = invite.invite_token
            
        invite_dict = {
            **invite.to_dict(),
            'role': invite.role.to_dict(),
            'invited_by': invite.invited_by.to_dict()
        }
        
        if status in ['accepted', 'declined']:
            # Decode and verify token
            logger.info('Decoding and verifying token')
            TokenService.decode_and_verify_token(
                db=db,
                token=invite_token,
                expected_token_type=TokenType.ORG_INVITE.value,
                credentials_exception=credentials_exception,
                check_user_id_in_payload=False
            )
        
        if status == 'accepted':
            email = invite.email
            # print(payload.get('email'))
            print(invite.email)
            organization_id = invite.organization_id
            # print(payload.get('organization_id'))
            print(invite.organization_id)
            
            # Check if user with email exists
            user = User.fetch_one_by_field(db, throw_error=False, email=email)
            
            if not user:
                logger.info('Creating new user')
                # Create the iser
                user, _, _ = UserService.create(
                    db=db,
                    payload=CreateUser(
                        email=email,
                        first_name='N/A',
                        last_name='N/A'
                    ),
                    bg_tasks=bg_tasks
                )
            
            # Check if user is already an organization member
            user_in_org = OrganizationMember.fetch_one_by_field(
                db=db, throw_error=False,
                user_id=user.id,
                organization_id=organization_id
            )
            
            if user_in_org:
                # Revoke token
                TokenService.revoke_token(db, invite_token, invite.inviter_id)
                raise HTTPException(400, 'User already exists in organization')
            
            # Add user to the organization
            logger.info('Adding user to organization')
            org_member = OrganizationMember.create(
                db=db,
                organization_id=organization_id,
                user_id=user.id,
                role_id=invite.role_id,
                is_primary_contact=False
            )
            
            organization = Organization.fetch_by_id(db, organization_id)
            
            # Convert all objects to be used in the email template into a dictionary because of db session that closes before the backgroud task is done
            user_dict = user.to_dict()
            organization_dict = organization.to_dict()
            # invite_dict = invite.__dict__.copy()
            # print(invite_dict)
            
            # TODO: Update the url
            bg_tasks.add_task(
                send_email,
                recipients=[user.email],
                template_name='organization-invite-accepted.html',
                subject=f'Welcome to {organization_dict["name"]}',
                template_data={
                    'user': user_dict,
                    'organization_url': f"{config('APP_URL')}/organizations/slug/{organization_dict['slug']}",
                    'join_date': org_member.join_date.date().strftime("%d %B %Y"),
                    'invite': invite_dict,
                    'organization': organization_dict
                }
            )
             
        # Update organization invite status
        logger.info(f"Updating status to {status}")
        OrganizationInvite.update(
            db=db,
            id=invite.id,
            status=status
        )
        
        # Revoke token
        TokenService.revoke_token(db, invite_token, invite.inviter_id)
    
    
    @classmethod
    def get_organization_roles(
        cls, 
        db: Session, 
        organization_id: str,
        page: int,
        per_page: int,
        sort_by: str,
        order: str,
        role_name: Optional[str] = None,
        include_default_roles: bool = True
    ):
        '''Function to get organization roles'''
        
        if include_default_roles:
            query = (
                db.query(OrganizationRole).filter(
                    or_(
                        OrganizationRole.organization_id == '-1',
                        OrganizationRole.organization_id == organization_id,
                    )
                )
            )
            
            if role_name:
                query = query.filter(OrganizationRole.role_name.ilike(f'%{role_name}%'))
            
            # query = query.order_by(OrganizationMember.join_date.desc())
            if order == "desc":
                query = query.order_by(desc(getattr(OrganizationRole, sort_by)))
            else:
                query = query.order_by(getattr(OrganizationRole, sort_by))
            
            count = query.count()

            # Handle pagination
            offset = (page - 1) * per_page
            roles = query.offset(offset).limit(per_page).all()
            return roles, count
            
        else:
            query, roles, count = OrganizationRole.fetch_by_field(
                db=db,
                sort_by=sort_by,
                order=order.lower(),
                page=page,
                per_page=per_page,
                search_fields={
                    'role_name': role_name
                },
                organization_id=organization_id,
            )
            
        return roles, count
    
    
    @classmethod
    def send_email_to_organization(
        cls, 
        db: Session, 
        bg_tasks: BackgroundTasks,
        organization_id: str,
        subject: str,
        template_name: Optional[str]= None,
        html_string: Optional[str]= None,
        context: dict = {},
        attachments: Optional[List[str]] = None
    ):
        '''This function is ised to send an email to an organization at once. Only Owners and Admins will receive the emails'''
        
        org_members, total = cls.get_organization_members(
            db=db,
            organization_id=organization_id,
            paginate=False,
            # page=1,
            # per_page=100,
            # sort_by='join_date',
            # order='desc'
        )
        
        # Get organization member emails if the member can receive emails through their permissioons
        org_member_emails = [member.user.email for member in org_members if 'email:receive' in member.role.permissions]
        logger.info(org_member_emails)
        
        # Send email to organization members
        bg_tasks.add_task(
            send_email,
            recipients=org_member_emails,
            template_name=template_name,
            html_template_string=html_string,
            subject=subject,
            template_data=context,
            attachments=attachments
        )
