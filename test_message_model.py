"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


from app import app
db.create_all()

class UserModelTestCase(TestCase):
    """Test Message Model.
    Ensuring the model works as expected."""
    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Remove all records from database tables."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        db.session.commit()

    def test_message_valid_info(self):
        """Does the Message model work with valid info?"""
        first_user= User(
            email="test11@test.com",
            username="testuser11",
            password="HASHED_PASSWORD"
        )
        id=123
        first_user.id= id

        db.session.add(first_user)
        db.session.commit()

        m = Message(text = 'test', user_id = id)
        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.user_id,id)
        self.assertEqual(m.text, 'test')
        self.assertEqual(len(first_user.messages),1)

    def test_message_missing_text(self):
        """Does the Message model fail without valid text?"""
        first_user= User(
            email="test11@test.com",
            username="testuser11",
            password="HASHED_PASSWORD"
        )
        id=123
        first_user.id= id

        db.session.add(first_user)
        db.session.commit()

        m = Message(text = None, user_id = id)
        with self.assertRaises(exc.SQLAlchemyError) as context:
            db.session.add(m)
            db.session.commit()

    def test_message_missing_user_id(self):
        """Does the Message model fail without valid user_id?"""
        first_user= User(
            email="test11@test.com",
            username="testuser11",
            password="HASHED_PASSWORD"
        )
        id=123
        first_user.id= id

        db.session.add(first_user)
        db.session.commit()

        m = Message(text = 'test', user_id = 321)
        with self.assertRaises(exc.SQLAlchemyError) as context:
            db.session.add(m)
            db.session.commit()