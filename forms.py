from flask_wtf import Form
from wtforms import (StringField, PasswordField, TextAreaField, BooleanField,
                    SelectField, IntegerField)
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email,
                               Length, EqualTo)
from wtforms.fields.html5 import DateField

import models


def tag_exists(form, field):
    for field_name, field_value in form.data.items():
        if field_name == "tag_label":
            if models.Tag.select().where(
                models.Tag.tag_label == field_value.upper()
            ).exists():
                raise ValidationError('Tag already exists.')


class NewEntry(Form):
    title = StringField(
        'Title',
        validators=[
            DataRequired()
        ]
    )
    date = DateField(
        'Date',
        #format='%m-%d-%Y',
        validators=[
            DataRequired()
        ]
    )
    time_spent_hours = IntegerField(
        'Hours',
        default=0
    )
    time_spent_minutes = IntegerField(
        'Minutes',
        default=0
    )
    what_i_learned = TextAreaField(
        'What I Learned',
        validators=[
            DataRequired()
        ]
    )
    resources_to_remember = TextAreaField(
        'Resources To Remember',
        validators=[
            DataRequired()
        ]
    )
    password = PasswordField(
        'New Password',
        validators=[
            EqualTo('password2', message='Passwords must match')
        ])
    password2 = PasswordField(
        'Confirm New Password',
    )


class NewTag(Form):
    tag_label = StringField(
        'Enter your new tag.',
        validators=[
            DataRequired(),
            tag_exists
        ]
    )


class Password(Form):
    password = PasswordField(
        'Password',
        validators=[
            DataRequired()
        ])
