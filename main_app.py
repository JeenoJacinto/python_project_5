from flask import (Flask, g, render_template, flash, redirect, url_for, abort,
                   request, send_file, send_from_directory)
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm as Form
from wtforms import (StringField, PasswordField, TextAreaField, BooleanField,
                    SelectField, IntegerField)
from wtforms.validators import (DataRequired, Regexp, ValidationError, Email,
                               Length, EqualTo)
from wtforms.fields.html5 import DateField

import forms
import models
from functions import slugify_title


app = Flask(__name__)
app.secret_key = "asdflanjl3242677293oljgs02932lnmdlsasdfv"


@app.before_request
def before_request():
    """
    Connect to database before each request.
    Creates global variables for the instance
    """
    g.db = models.DATABASE
    g.db.connect()


@app.after_request
def after_request(response):
    """Close the database connectinon after each request."""
    g.db.close()
    return response


@app.route('/redirect_edit/<int:entry_id>/<tags_or_details>')
def redirect_edit(entry_id, tags_or_details):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    return redirect(
        url_for(
        'edit',
        tags_or_details=tags_or_details,
        entry_id=chosen_entry.journal_id,
        slug=slugify_title(chosen_entry.title)
        )
    )


@app.route(
    '/edit/<tags_or_details>/<int:entry_id>/<slug>', methods=('GET', 'POST')
)
def edit(tags_or_details, entry_id, slug):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    if chosen_entry.has_password:
        entry_password = models.JournalPassword.select().where(
            models.JournalPassword.journal_entry == chosen_entry
        ).get().password
        password_form = forms.Password()
        if password_form.validate_on_submit():
            if check_password_hash(entry_password, password_form.password.data):
                flash("Correct Password Entered!", "success")
                if tags_or_details == "tags":
                    return redirect(
                        url_for(
                            'set_tag',
                            entry_id=entry_id,
                            slug=slugify_title(chosen_entry.title)
                        )
                    )
                elif tags_or_details == "details":
                    session_bool = models.SessionBool.select().get()
                    # the session bool protects the details edit page from
                    # being accessed by simply typing the url
                    session_bool.switch = True
                    session_bool.save()
                    return redirect(
                        url_for(
                            'editdetails',
                            entry_id=entry_id,
                            slug=slugify_title(chosen_entry.title)
                        )
                    )
            else:
                flash("Incorrect Password", "fail")
                return redirect(url_for(
                    'redirect_details', entry_id=chosen_entry.journal_id
                ))
        return render_template("entry_password.html", form=password_form)
    else:
        if tags_or_details == "tags":
            return redirect(
                url_for(
                    'set_tag',
                    entry_id=entry_id,
                    slug=slugify_title(chosen_entry.title)
                )
            )
        elif tags_or_details == "details":
            class EditEntry(Form):
                """Form with dynamic select fields to set defaults"""
                pass
            setattr(
                EditEntry,
                "title",
                StringField(
                    u'Title',
                    validators=[DataRequired()],
                    default=chosen_entry.title
                )
            )
            setattr(
                EditEntry,
                "date",
                DateField(
                    u'Date',
                    validators=[DataRequired()],
                    default=chosen_entry.date
                )
            )
            setattr(
                EditEntry,
                "time_spent_hours",
                IntegerField(
                    u'Hours',
                    default=chosen_entry.time_spent_hours
                )
            )
            setattr(
                EditEntry,
                "time_spent_minutes",
                IntegerField(
                    u'Minutes',
                    default=chosen_entry.time_spent_minutes
                )
            )
            setattr(
                EditEntry,
                "what_i_learned",
                TextAreaField(
                    u'What I Learned',
                    validators=[DataRequired()],
                    default=chosen_entry.what_i_learned
                )
            )
            setattr(
                EditEntry,
                "resources_to_remember",
                TextAreaField(
                    u'Resources to Remember',
                    validators=[DataRequired()],
                    default=chosen_entry.resources_to_remember
                )
            )
            setattr(
                EditEntry,
                "password",
                PasswordField(
                    u'Password',
                    validators=[
                        EqualTo('password2', message='Passwords must match')
                    ]
                )
            )
            setattr(
                EditEntry,
                "password2",
                PasswordField(u'Password2')
            )
            form = EditEntry()
            if form.validate_on_submit():
                if form.password.data:
                    chosen_entry.title = form.title.data
                    chosen_entry.date = form.date.data
                    chosen_entry.time_spent_hours = form.time_spent_hours.data
                    chosen_entry.time_spent_minutes = form.time_spent_minutes.data
                    chosen_entry.what_i_learned = form.what_i_learned.data
                    chosen_entry.resources_to_remember = form.resources_to_remember.data
                    chosen_entry.has_password = True
                    chosen_entry.save()
                    password_model = models.JournalPassword.select().where(
                        models.JournalPassword.journal_entry == chosen_entry
                    ).get()
                    password_model.password = generate_password_hash(
                        form.password.data
                    )
                    password_model.save()
                else:
                    chosen_entry.title = form.title.data
                    chosen_entry.date = form.date.data
                    chosen_entry.time_spent_hours = form.time_spent_hours.data
                    chosen_entry.time_spent_minutes = form.time_spent_minutes.data
                    chosen_entry.what_i_learned = form.what_i_learned.data
                    chosen_entry.resources_to_remember = form.resources_to_remember.data
                    chosen_entry.has_password = False
                    chosen_entry.save()
                flash("Details Updated!", "success")
                return redirect(
                    url_for(
                        'redirect_details',
                        entry_id=chosen_entry.journal_id
                    )
                )
            return render_template(
                "edit.html",
                form=form,
                chosen_entry=chosen_entry
            )
        else:
            return redirect(url_for(index))


@app.route('/editdetails/<int:entry_id>/<slug>', methods=('GET', 'POST'))
def editdetails(entry_id, slug):
    session_bool = models.SessionBool.select().get()
    if session_bool.switch: # checks if accessed by entering password
        chosen_entry = models.JournalEntry.select().where(
            models.JournalEntry.journal_id == entry_id
        ).get()
        class EditEntry(Form):
            """Form with dynamic select fields to set defaults"""
            pass
        setattr(
            EditEntry,
            "title",
            StringField(
                u'Title',
                validators=[DataRequired()],
                default=chosen_entry.title
            )
        )
        setattr(
            EditEntry,
            "date",
            DateField(
                u'Date',
                validators=[DataRequired()],
                default=chosen_entry.date
            )
        )
        setattr(
            EditEntry,
            "time_spent_hours",
            IntegerField(
                u'Hours',
                default=chosen_entry.time_spent_hours
            )
        )
        setattr(
            EditEntry,
            "time_spent_minutes",
            IntegerField(
                u'Minutes',
                default=chosen_entry.time_spent_minutes
            )
        )
        setattr(
            EditEntry,
            "what_i_learned",
            TextAreaField(
                u'What I Learned',
                validators=[DataRequired()],
                default=chosen_entry.what_i_learned
            )
        )
        setattr(
            EditEntry,
            "resources_to_remember",
            TextAreaField(
                u'Resources to Remember',
                validators=[DataRequired()],
                default=chosen_entry.resources_to_remember
            )
        )
        setattr(
            EditEntry,
            "password",
            PasswordField(
                u'Password',
                validators=[
                    EqualTo('password2', message='Passwords must match')
                ]
            )
        )
        setattr(
            EditEntry,
            "password2",
            PasswordField(u'Password2')
        )
        form = EditEntry()
        if form.validate_on_submit():
            session_bool.switch = False
            session_bool.save()
            # Relocks session bool to require a password if accessed again
            # Only relocks when form is validated on submit unfortunately
            if form.password.data:
                chosen_entry.title = form.title.data
                chosen_entry.date = form.date.data
                chosen_entry.time_spent_hours = form.time_spent_hours.data
                chosen_entry.time_spent_minutes = form.time_spent_minutes.data
                chosen_entry.what_i_learned = form.what_i_learned.data
                chosen_entry.resources_to_remember = form.resources_to_remember.data
                chosen_entry.has_password = True
                chosen_entry.save()
                password_model = models.JournalPassword.select().where(
                    models.JournalPassword.journal_entry == chosen_entry
                ).get()
                password_model.password = generate_password_hash(form.password.data)
                password_model.save()
            else:
                chosen_entry.title = form.title.data
                chosen_entry.date = form.date.data
                chosen_entry.time_spent_hours = form.time_spent_hours.data
                chosen_entry.time_spent_minutes = form.time_spent_minutes.data
                chosen_entry.what_i_learned = form.what_i_learned.data
                chosen_entry.resources_to_remember = form.resources_to_remember.data
                chosen_entry.has_password = False
                chosen_entry.save()
            flash("Details Updated!", "success")
            return redirect(
                url_for(
                'redirect_details',
                entry_id=chosen_entry.journal_id
                )
            )
        return render_template(
            "edit.html",
            form=form,
            chosen_entry=chosen_entry
        )
    else:
        flash("Access Denied!", "fail")
        return redirect(url_for('index'))


@app.route('/redirect_delete/<int:entry_id>')
def redirect_delete(entry_id):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    return redirect(
        url_for('delete',
        entry_id=chosen_entry.journal_id,
        slug=slugify_title(chosen_entry.title)
        )
    )


@app.route('/delete/<int:entry_id>/<slug>', methods=('GET', 'POST'))
def delete(entry_id, slug):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    if chosen_entry.has_password:
        entry_password = models.JournalPassword.select().where(
            models.JournalPassword.journal_entry == chosen_entry
        ).get().password
        password_form = forms.Password()
        if password_form.validate_on_submit():
            if check_password_hash(entry_password, password_form.password.data):
                flash("Correct Password Entered!", "success")
                entry_title = chosen_entry.title
                entry_date = chosen_entry.date.strftime('%B %d, %Y')
                tag_list = []
                for tag in models.TagToJournal.select().where(
                    models.TagToJournal.journal == chosen_entry
                ):
                    tag_list.append(tag.tag_label)
                session_bool = models.SessionBool.select().get()
                session_bool.switch = True
                session_bool.save()
                return render_template(
                    'delete.html',
                    entry_title=entry_title,
                    entry_date=entry_date,
                    tag_list=tag_list,
                    entry_id=entry_id
                )
            else:
                flash("Incorrect Password", "fail")
                return redirect(
                    url_for(
                        'redirect_details',
                        entry_id=chosen_entry.journal_id
                    )
                )
        return render_template("entry_password.html", form=password_form)
    else:
        entry_title = chosen_entry.title
        entry_date = chosen_entry.date.strftime('%B %d, %Y')
        tag_list = []
        for tag in models.TagToJournal.select().where(
            models.TagToJournal.journal == chosen_entry
        ):
            tag_list.append(tag.tag_label)
        return render_template(
            'delete.html',
            entry_title=entry_title,
            entry_date=entry_date,
            tag_list=tag_list,
            entry_id=entry_id
        )


@app.route('/delete_entry/<int:entry_id>')
def delete_entry(entry_id):
    session_bool = models.SessionBool.select().get()
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    if chosen_entry.has_password:
        if session_bool.switch:
            session_bool.switch = False
            session_bool.save()
            chosen_entry.delete_instance()
            for tag in models.TagToJournal.select().where(
                models.TagToJournal.journal == chosen_entry
            ):
                tag.delete_instance()
                # delete all previously associated tags
            flash("Entry Deleted!", "success")
            return redirect(url_for('index'))
        else:
            flash("Access Denied", "fail")
            return redirect(url_for(index))
    else:
        chosen_entry.delete_instance()
        return redirect(url_for('index'))


@app.route('/redirect_set_tag/<int:entry_id>')
def redirect_set_tag(entry_id):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    return redirect(
        url_for(
            'set_tag',
            entry_id=chosen_entry.journal_id,
            slug=slugify_title(chosen_entry.title)
        )
    )


@app.route('/set_tag/<int:entry_id>/<slug>')
def set_tag(entry_id, slug):
    selected_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    associated_tag_labels = [] # stores strings of tag labels that are linked to current journal
    all_tags = models.Tag.select()
    associated_tags = models.TagToJournal.select().where(
        models.TagToJournal.journal == selected_entry
    )
    current_associated_tags = [] # list of model tags that are chosen to be associated with entry
    non_current_associated_tags = [] # list of model tags that are weren't chosen to be associated with entry
    for tag in associated_tags: # gets all tag label strings and appends it to associated_tag_lables
        associated_tag_labels.append(tag.tag_label)
    for tag in all_tags: # sort models into current_associated_tags list
        if tag.tag_label in associated_tag_labels:
            current_associated_tags.append(tag)
        else:
            non_current_associated_tags.append(tag)
    return render_template(
        "tag.html",
        used_tags=current_associated_tags,
        non_used_tags=non_current_associated_tags,
        entry_id=entry_id,
        entry=selected_entry
    )


@app.route('/setting_tag/<int:entry_id>/<tag_name>')
def setting_tag(entry_id, tag_name):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    models.TagToJournal.create(
        journal = chosen_entry,
        tag_label = tag_name
    )
    return redirect(
        url_for(
            'set_tag',
            entry_id=entry_id,
            slug=slugify_title(chosen_entry.title)
        )
    )


@app.route('/unsetting_tag/<int:entry_id>/<tag_name>')
def unsetting_tag(entry_id, tag_name):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    models.TagToJournal.select().where(
        (models.TagToJournal.journal == chosen_entry) &
        (models.TagToJournal.tag_label == tag_name)
    ).get().delete_instance()
    return redirect(
        url_for(
            'set_tag',
            entry_id=entry_id,
            slug=slugify_title(chosen_entry.title)
        )
    )


@app.route('/new_tag', methods=('GET', 'POST'))
def new_tag():
    locked_unlocked = models.PasswordForAdd.select().get().locked
    if locked_unlocked:
        return redirect(url_for('lock', previous_page='new_tag'))
    else:
        form = forms.NewTag()
        if form.validate_on_submit():
            models.Tag.create(
                tag_label = form.tag_label.data.upper()
            )
            return redirect(url_for("index"))
        return render_template("new_tag.html", form=form)


@app.route('/new', methods=('GET', 'POST'))
def new():
    locked_unlocked = models.PasswordForAdd.select().get().locked
    if locked_unlocked:
        return redirect(url_for('lock', previous_page='new'))
    else:
        form = forms.NewEntry()
        unique_id_model = models.UniqueIdConstant.select().get()
        plus_1 = unique_id_model.new_id + 1
        unique_id_model.new_id = plus_1
        unique_id_model.save()
        unique_id = unique_id_model.new_id
        if form.validate_on_submit():
            if form.password.data:
                models.JournalEntry.create(
                    journal_id = unique_id,
                    title = form.title.data,
                    date = form.date.data,
                    time_spent_hours = form.time_spent_hours.data,
                    time_spent_minutes = form.time_spent_minutes.data,
                    what_i_learned = form.what_i_learned.data,
                    resources_to_remember = form.resources_to_remember.data,
                    has_password = True
                )
                models.JournalPassword.create_password(
                    journal_entry = models.JournalEntry.select().where(
                        models.JournalEntry.journal_id == unique_id
                    ).get(),
                    password = form.password.data
                )
            else:
                models.JournalEntry.create(
                    journal_id = unique_id,
                    title = form.title.data,
                    date = form.date.data,
                    time_spent_hours = form.time_spent_hours.data,
                    time_spent_minutes = form.time_spent_minutes.data,
                    what_i_learned = form.what_i_learned.data,
                    resources_to_remember = form.resources_to_remember.data,
                    has_password = False
                )
            return redirect(
                url_for(
                    'set_tag',
                    entry_id=unique_id,
                    slug=slugify_title(form.title.data)
                )
            )
        return render_template('new.html', form=form)


@app.route('/lock/<previous_page>', methods=('GET', 'POST'))
def lock(previous_page):
    form = forms.Password()
    password_model = models.PasswordForAdd.select().get()
    if password_model.locked == True:
        if form.validate_on_submit():
            if check_password_hash(password_model.password, form.password.data):
                password_model.locked = False
                password_model.save()
                flash("Add features unlocked!", "success")
            else:
                flash("Incorrect Password", "fail")
            return redirect(url_for(previous_page))
        return render_template("unlock.html", form=form)
    else:
        return render_template("lock.html")


@app.route('/lock_confirm')
def lock_confirm():
    password_model = models.PasswordForAdd.select().get()
    password_model.locked = True
    password_model.save()
    flash("Add features locked!", "success")
    return redirect(url_for("index"))


@app.route('/redirect_details/<int:entry_id>')
def redirect_details(entry_id):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    return redirect(
        url_for(
            'details',
            entry_id=chosen_entry.journal_id,
            slug=slugify_title(chosen_entry.title)
        )
    )


@app.route('/details/<int:entry_id>/<slug>')
def details(entry_id, slug):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    entry_title = chosen_entry.title
    entry_date = chosen_entry.date.strftime('%B %d, %Y')
    entry_time_spent = "{} hours {} minutes".format(
        str(chosen_entry.time_spent_hours),
        str(chosen_entry.time_spent_minutes)
    )
    unfmt_entry_learned = chosen_entry.what_i_learned
    entry_learned = unfmt_entry_learned.splitlines() # delineates new lines and line breaks
    unfmt_entry_sources = chosen_entry.resources_to_remember
    entry_sources = unfmt_entry_sources.splitlines() # delineates new lines and line breaks
    tag_list = []
    for tag in models.TagToJournal.select().where(
        models.TagToJournal.journal == chosen_entry
    ):
        tag_list.append(tag.tag_label)
    return render_template(
        'detail.html',
        entry_title=entry_title,
        entry_date=entry_date,
        entry_time_spent=entry_time_spent,
        entry_learned=entry_learned,
        entry_sources=entry_sources,
        tag_list=tag_list,
        entry_id=entry_id
    )


@app.route('/redirect_tag_details/<int:entry_id>')
def redirect_tag_details(entry_id):
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    return redirect(
        url_for(
        'tag_details',
        entry_id=chosen_entry.journal_id,
        slug=slugify_title(chosen_entry.title)
        )
    )


@app.route('/tag_details/<int:entry_id>/<slug>')
def tag_details(entry_id, slug):
    # generates a list of specific tags associated with chosen entry
    # generates another list of entries that share tags with chosen entry
    chosen_entry = models.JournalEntry.select().where(
        models.JournalEntry.journal_id == entry_id
    ).get()
    entry_title = chosen_entry.title
    entry_date = chosen_entry.date.strftime('%B %d, %Y')
    entry_tags = []
    for tag in models.TagToJournal.select().where(
        models.TagToJournal.journal == chosen_entry
    ):
        entry_tags.append(tag.tag_label)
    associated_tags_dict = {} # dict of which journal entries has which tags
    # {1:sports, 1:business, ect} key are the journal unique id's
    all_journal_entries = models.JournalEntry.select()
    for entry in all_journal_entries:
        tag_list = []
        for tag in models.TagToJournal.select().where(
            models.TagToJournal.journal == entry
        ):
            # finds all tags linked to entry
            tag_list.append(tag.tag_label)
        associated_tags_dict[entry.journal_id] = tag_list
            # creates the dict of entry id to tag label
    shared_tags = [] # Associated tags with chosen entry
    tag_shared_entries = [] # IDs of journal entries that share tags -
                            # with chosen entry
    for id_entry, tag_name in associated_tags_dict.items():
        if chosen_entry.journal_id == id_entry:
            for tag_label in tag_name:
                shared_tags.append(tag_label)
            # get tags associated with chosen entry
    for id_entry, tag_name in associated_tags_dict.items():
        if id_entry != entry_id:
            for tag_label in tag_name:
                if tag_label in shared_tags:
                    tag_shared_entries.append(id_entry)
                    break
                    # gathers entries that share tags with chosen entry
    related_journal_entries = models.JournalEntry.select().where(
        models.JournalEntry.journal_id << tag_shared_entries
    )
    return render_template(
        "tag_details.html",
        entry_id=entry_id,
        entry_title=entry_title,
        entry_date=entry_date,
        tag_list=entry_tags,
        shared_tags=shared_tags,
        all_journal_entries=related_journal_entries,
        associated_tags_dict=associated_tags_dict
    )


@app.route('/')
def index():
    associated_tags_dict = {} # dict of which journal entries has which tags
    # {1:sports, 1:business, ect} key are the journal unique id's
    all_journal_entries = models.JournalEntry.select()
    for entry in all_journal_entries:
        tag_list = []
        for tag in models.TagToJournal.select().where(
            models.TagToJournal.journal == entry
        ):
            # finds all tags linked to entry
            tag_list.append(tag.tag_label)
        associated_tags_dict[entry.journal_id] = tag_list
            # creates the dict of entry id to tag label
    return render_template(
        "index.html",
        all_journal_entries=all_journal_entries,
        associated_tags_dict=associated_tags_dict
    )


if __name__ == '__main__':
    models.initialize()
    if not models.PasswordForAdd.select().exists():
        models.PasswordForAdd.create_password(
            password='password',
            locked=True
        )
    if not models.SessionBool.select().exists():
        models.SessionBool.create(
            switch=False
        )
    if not models.UniqueIdConstant.select().exists():
        models.UniqueIdConstant.create(
            new_id=0
        )
    app.run(debug=True)
