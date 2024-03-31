"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        """Remove all records from database tables."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        db.session.commit()

    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message(self):
        """Can user delete a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Before we delete any messages, let's first post a message because the database is empty due to the teardown method.
            resp_add = c.post("/messages/new", data={"text": "Hello"})
            
            added_message = Message.query.filter_by(user_id = self.testuser.id).one()
            added_message_id=added_message.id
            resp_delete = c.post(f"messages/{added_message_id}/delete")

            # redirect 302
            self.assertEqual(resp_delete.status_code, 302)

            message_after_delete = Message.query.filter_by(user_id = self.testuser.id).one_or_none()
            self.assertEqual(message_after_delete, None)

    def test_add_unauthorized(self):
        """When a user is logged out, they can't add a message"""
        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # we're checking the flash message (resp.data)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_delete_unauthorized(self):
        """When a user is logged out, they can't delete a message"""
        message_id = 9999
        new= Message(id = message_id, text = "hello", user_id = self.testuser.id)
        db.session.add(new)
        db.session.commit()
        with self.client as c:
            resp = c.post(f"messages/{message_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            # we're checking the flash message (resp.data)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_message_as_another_user(self):
        """when a user is logged in, they can't add a message as another user"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123123 #fake id

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects= True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_message_delete(self):
        """when a user is logged in, they can't add a message as another user"""
        # A fake user that will try to delete the message
        u = User.signup(username="fake-user",
                        email="faketest@test.com",
                        password="password",
                        image_url=None)
        u.id = 76543

        #Message is owned by testuser
        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )
        db.session.add(u)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543

            resp = c.post("/messages/1234/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m = Message.query.get(1234)
            self.assertIsNotNone(m)
