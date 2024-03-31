"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
# from bs4 import BeautifulSoup


os.environ['DATABASE_URL'] = "postgresql:///warbler-test"




from app import app, CURR_USER_KEY

db.create_all()



app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    """Test views for messages."""
    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("user1", "test1@test.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("user2", "test2@test.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("user3", "test3@test.com", "password", None)
        self.u3_id = 885
        self.u3.id = self.u3_id
        self.u4 = User.signup("user4", "test4@test.com", "password", None)
        self.u4_id = 886
        self.u4.id = self.u4_id

        db.session.commit()

    def tearDown(self):
        """delete everything in the database after each function"""
        resp = super().tearDown()
        db.session.rollback()
        return resp
    
    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@user1", str(resp.data))
            self.assertIn("@user2", str(resp.data))
            self.assertIn("@user3", str(resp.data))
            self.assertIn("@user4", str(resp.data))

    def test_homepage(self):
        """If the user is not logged in, show them the logged out homepage.
        If the user is logged in, show them the logged in homepage"""

        with self.client as c:
            resp = c.get('/', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>',html)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp2 = c.get('/', follow_redirects=True)
            html = resp2.get_data(as_text=True)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn('<a href="/logout">Log out</a>',html)
    
    def test_user_view_follower_page_logged_in(self):
        """When a user is logged in, they can see the follower pages for any user."""
        follow = Follows(user_being_followed_id=self.u1_id, user_following_id=self.u2_id)
        db.session.add(follow)
        db.session.commit()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # followers
            resp= c.get(f'/users/{self.u1_id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'<p>@{self.u2.username}</p>',html)

            #followings
            resp2 = c.get(f'/users/{self.u2_id}/following', follow_redirects=True)
            html = resp2.get_data(as_text=True)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn(f'<p>@{self.u1.username}</p>',html)
    
    def test_user_view_followers_page_logged_out(self):
        """When a user is logged out, they can't see the follower pages"""
        follow = Follows(user_being_followed_id=self.u1_id, user_following_id=self.u2_id)
        db.session.add(follow)
        db.session.commit()
        with self.client as c:
            
            # follower page
            resp = c.get(f'/users/{self.u1_id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>',html)

            # following page
            resp2 = c.get(f'/users/{self.u2_id}/following', follow_redirects=True)
            html2 = resp2.get_data(as_text=True)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn('<p>Sign up now to get your own personalized timeline!</p>',html2)

    def test_signup_page(self):
        """test sign up page
        If the user is already logged in, redirect user to homepage"""
        with self.client as c:
            resp = c.get('/signup', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Join Warbler today.',html)

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp2 = c.get('/signup', follow_redirects=True)
            html2 = resp2.get_data(as_text=True)
            self.assertEqual(resp2.status_code, 200)
            self.assertIn('<a href="/logout">Log out</a>',html2)

                        
    def test_show_user_profile(self):
        """test user's profile"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f'/users/{self.testuser.id}', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(f'@{self.testuser.username}',html)

    def test_show_following_page(self):
        """test following page of a user"""
        follow1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        follow2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        follow3 = Follows(user_being_followed_id=self.u3_id, user_following_id=self.testuser_id)
        follow4 = Follows(user_being_followed_id=self.u4_id, user_following_id=self.testuser_id)

        db.session.add_all([follow1,follow2,follow3,follow4])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f'/users/{self.testuser.id}/following', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn(f'@{self.u1.username}',html)
            self.assertIn(f'@{self.u2.username}',html)
            self.assertIn(f'@{self.u3.username}',html)
            self.assertIn(f'@{self.u4.username}',html)

    def test_show_follower_page(self):
        """test follower page of a user"""
        follow1 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)
        follow2 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u2_id)
        follow3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u3_id)
        follow4 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u4_id)

        db.session.add_all([follow1,follow2,follow3,follow4])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f'/users/{self.testuser.id}/followers', follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn(f'@{self.u1.username}',html)
            self.assertIn(f'@{self.u2.username}',html)
            self.assertIn(f'@{self.u3.username}',html)
            self.assertIn(f'@{self.u4.username}',html)
