"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test User Model."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        """Remove all records from database tables."""
        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        db.session.commit()

    def test_user_model(self):
        """Does basic model work?"""

        first_user= User(
            email="test11@test.com",
            username="testuser11",
            password="HASHED_PASSWORD"
        )

        db.session.add(first_user)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(first_user.messages), 0)
        self.assertEqual(len(first_user.followers), 0)

        #testing the repr method
        self.assertEqual(repr(first_user), f"<User #{first_user.id}: {first_user.username}, {first_user.email}>")

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?
        - is_following() function should return True

        Does is_following successfully detect when user1 is NOT following user2?
        - is_following() function should return False"""

        first_user= User(
            email="test11@test.com",
            username="testuser11",
            password="HASHED_PASSWORD"
        )
        second_user= User(
            email="test22@test.com",
            username="testuser22",
            password="HASHED_PASSWORD"
        )

        db.session.add(first_user)
        db.session.add(second_user)
        db.session.commit()

        first_user_id = first_user.id
        second_user_id = second_user.id

        new_follow = Follows(
            user_being_followed_id = second_user_id,
            user_following_id = first_user_id
        )
        db.session.add(new_follow)
        db.session.commit()


        self.assertTrue(first_user.is_following(second_user))
        
        db.session.delete(new_follow)
        db.session.commit()
        self.assertFalse(first_user.is_following(second_user))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?
        - is_followed_by() function should return True

        Does is_followed_by successfully detect when user1 is not followed by user2?
        - is_followed_by() function should return False"""

        first_user= User(
            email="test11@test.com",
            username="testuser11",
            password="HASHED_PASSWORD"
        )
        second_user= User(
            email="test22@test.com",
            username="testuser22",
            password="HASHED_PASSWORD"
        )

        db.session.add(first_user)
        db.session.add(second_user)
        db.session.commit()

        first_user_id = first_user.id
        second_user_id = second_user.id

        new_follow = Follows(
            user_being_followed_id = second_user_id,
            user_following_id = first_user_id
        )
        db.session.add(new_follow)
        db.session.commit()


        self.assertTrue(second_user.is_followed_by(first_user))
        
        db.session.delete(new_follow)
        db.session.commit()
        self.assertFalse(second_user.is_followed_by(first_user))

    def test_sign_up_valid_info(self):
        """Does User.signup successfully create a new user given valid credentials?"""
        username = 'Test'
        email = 'test@gmail.com'
        password = 'secret123'
        image_url = None
        user = User.signup(
                username=username,
                password=password,
                email=email,
                image_url=image_url,
            )
        id =99999
        user.id = id
        
        db.session.commit()

        user_from_database = User.query.filter_by(id = id).first()

        self.assertEqual(user_from_database.username, username)
        self.assertEqual(user_from_database.email, email)
        # because we use bcrypt to hash the password 
        self.assertNotEqual(user_from_database.password, password)
    
    def test_sign_up_invalid_username(self):
        """Does User.signup fail when the username is invalid?"""
        user = User.signup(None, "test@test.com", "password", None)
        id = 123456789
        user.id = id
        with self.assertRaises(exc.SQLAlchemyError) as context:
            db.session.commit()

    def test_sign_up_not_unique_username(self):
        """Does User.signup fail when the username is not unique?"""
        user = User.signup("same123", "test@test.com", "password", None)
        id = 123456789
        user.id = id
        db.session.commit()

        user2 = User.signup("same123", "test2@test.com", "password", None)
        id2 = 123123
        user2.id = id2
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    

    def test_sign_up_invalid_email(self):
        """Does User.signup fail when the email is invalid?"""
        user = User.signup("chicken123", None, "password", None)
        id = 123456789
        user.id = id
        with self.assertRaises(exc.SQLAlchemyError) as context:
            db.session.commit()

    def test_sign_up_invalid_password(self):
        """Does User.signup fail when the password is invalid?"""
        with self.assertRaises(ValueError) as context:
            # ValueError: Password must be non-empty.
            User.signup("testtest", "email@email.com", "", None)

    def test_authentication(self):
        """Does User.authenticate work with valid info?
        Does User.authenticate fail with invalid into?"""
        username = 'Test'
        email = 'test@gmail.com'
        password = 'secret123'
        image_url = None
        user = User.signup(
                username=username,
                password=password,
                email=email,
                image_url=image_url,
            )
        id =99999
        user.id = id
        
        db.session.commit()
        # valid info
        self.assertTrue(User.authenticate(username, password))
        # wrong username
        self.assertFalse(User.authenticate('test2', password))
        # wrong password
        self.assertFalse(User.authenticate(username, 'wrongpassword'))