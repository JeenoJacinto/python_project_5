from peewee import *
from flask_bcrypt import generate_password_hash, check_password_hash

DATABASE = SqliteDatabase('journal.db')

class JournalEntry(Model):
    journal_id = IntegerField(unique=True)
    title = CharField()
    date = DateField()
    time_spent_hours = IntegerField()
    time_spent_minutes = IntegerField()
    what_i_learned = TextField()
    resources_to_remember = TextField()
    has_password = BooleanField()

    class Meta:
        database = DATABASE


class JournalPassword(Model):
    journal_entry = ForeignKeyField(rel_model=JournalEntry)
    password = CharField()

    class Meta:
        database = DATABASE

    @classmethod
    def create_password(cls, journal_entry, password):
        try:
            with DATABASE.transaction():
                cls.create(
                    journal_entry=journal_entry,
                    password=generate_password_hash(password)
                )
        except IntegrityError:
            # happens when email or username is in use
            raise ValueError("Journal already exists")


class PasswordForAdd(Model):
    password = CharField()
    locked = BooleanField()

    class Meta:
        database = DATABASE

    @classmethod
    def create_password(cls, password, locked):
        try:
            with DATABASE.transaction():
                cls.create(
                    password=generate_password_hash(password),
                    locked=True
                )
        except IntegrityError:
            # happens when email or username is in use
            raise ValueError("Journal already exists")


class Tag(Model):
    tag_label = CharField(unique=True)

    class Meta:
        database = DATABASE


class TagToJournal(Model):
    journal = ForeignKeyField(rel_model=JournalEntry)
    tag_label = CharField()

    class Meta:
        database = DATABASE


class SessionBool(Model):
    switch = BooleanField()

    class Meta:
        database = DATABASE


class UniqueIdConstant(Model):
    new_id = IntegerField()

    class Meta:
        database = DATABASE


def initialize():
    DATABASE.connect()
    DATABASE.create_tables(
        [
            JournalEntry,
            JournalPassword,
            Tag,
            TagToJournal,
            PasswordForAdd,
            SessionBool,
            UniqueIdConstant
        ], safe=True
    )
    DATABASE.close()
