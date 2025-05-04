import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.orm import relationship, Session

from api.core.base.base_model import BaseTableModel
from api.v1.schemas.project import Priority, ProjectStatus


class Project(BaseTableModel):
    __tablename__ = 'projects'

    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    organization_id = sa.Column(sa.String, sa.ForeignKey("organizations.id"), index=True)
    department_id = sa.Column(sa.String, sa.ForeignKey("departments.id"), index=True)
    creator_id = sa.Column(sa.String, sa.ForeignKey("users.id"), nullable=False)
    start_date = sa.Column(sa.DateTime)
    end_date = sa.Column(sa.DateTime)
    status = sa.Column(sa.String, default=ProjectStatus.not_started.value, index=True)
    slug = sa.Column(sa.String, index=True, unique=True)
    logo_url = sa.Column(sa.String)
    additional_info = sa.Column(sa.JSON, default={})

    organization = relationship('Organization')
    creator = relationship(
        "User", 
        backref='created_projects', 
        uselist=False, 
        lazy='selectin',
        
    )
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    members = relationship(
        'User',
        secondary='project_members',
        primaryjoin="and_(Project.id==ProjectMember.project_id, ProjectMember.is_active==True)",
        secondaryjoin="and_(ProjectMember.user_id==User.id, User.is_deleted==False, User.is_active==True)",
        backref='user_projects',
        lazy="selectin"
    )
    attachments = relationship(
        'File',
        primaryjoin='and_(Project.id==foreign(File.model_id), File.is_deleted==False)',
        lazy='selectin',
        backref='projects'
    )


class Task(BaseTableModel):
    __tablename__ = "tasks"
    
    project_id = sa.Column(sa.String, sa.ForeignKey("projects.id"), index=True, nullable=False)
    creator_id = sa.Column(sa.String, sa.ForeignKey("users.id"), nullable=False)
    parent_id = sa.Column(sa.String, sa.ForeignKey('tasks.id'))
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    priority = sa.Column(sa.String, default=Priority.medium.value, index=True)
    status = sa.Column(sa.String, default=ProjectStatus.not_started.value, index=True)
    due_date = sa.Column(sa.DateTime)
    additional_info = sa.Column(sa.JSON, default={})

    project = relationship("Project", back_populates="tasks", uselist=False)
    creator = relationship(
        "User", 
        backref='created_tasks', 
        uselist=False, 
        lazy='selectin',
    )
    assignees = relationship(
        "User",
        secondary='task_assignees',
        primaryjoin="and_(Task.id==TaskAssignee.task_id, TaskAssignee.is_active==True)",
        secondaryjoin="and_(TaskAssignee.user_id==User.id, User.is_deleted==False, User.is_active==True)",
        backref='user_tasks',
        lazy="selectin"
    )
    sub_tasks = relationship(
        'Task',
        remote_side='Task.id',
        foreign_keys=[parent_id],
        backref='child_tasks',
        lazy="selectin"
    )
    attachments = relationship(
        'File',
        primaryjoin='and_(Task.id==foreign(File.model_id), File.is_deleted==False)',
        lazy='selectin',
        backref='tasks'
    )


class Milestone(BaseTableModel):
    __tablename__ = "project_milestones"

    project_id = sa.Column(sa.String, sa.ForeignKey("projects.id"), index=True)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text)
    due_date = sa.Column(sa.DateTime)

    project = relationship("Project", back_populates="milestones")
    

class ProjectMember(BaseTableModel):
    __tablename__ = 'project_members'
    
    user_id = sa.Column(sa.String, sa.ForeignKey('users.id'), index=True, nullable=False)
    project_id = sa.Column(sa.String, sa.ForeignKey('projects.id'), index=True, nullable=False)
    role = sa.Column(sa.String, nullable=False)  # owner, admin, member, viewer
    is_active = sa.Column(sa.Boolean, server_default='true')
    

class TaskAssignee(BaseTableModel):
    __tablename__ = 'task_assignees'
    
    user_id = sa.Column(sa.String, sa.ForeignKey('users.id'), index=True)
    task_id = sa.Column(sa.String, sa.ForeignKey('tasks.id'), index=True)
    is_active = sa.Column(sa.Boolean, server_default='true')
