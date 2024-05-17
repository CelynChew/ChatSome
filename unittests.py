import unittest

from app import app, db
from app.models import User, Chats, UserChat, Message
from config import TestConfig
import os
from datetime import datetime
from io import BytesIO

class TestUserModel(unittest.TestCase):
    def setUp(self):
        os.environ['FLASK_ENV'] = 'test'
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all() # Create tables in the test database

    def tearDown(self):
        db.session.remove()
        db.drop_all() # Drop tables after testing
        self.app_context.pop()

    # Test for username uniquess
    def test_username_uniqueness(self):
        # Create a user with a unique username
        user1 = User(username='test_user', password='password')
        db.session.add(user1)
        db.session.commit()

        # Attempt to create another user with the same username
        user2 = User(username='test_user', password='password')
        db.session.add(user2)

        # Assert that adding the second user raises an IntegrityError
        with self.assertRaises(Exception) as context:
            db.session.commit()
        self.assertTrue('UNIQUE constraint failed: user.username' in str(context.exception))

    # Test for login validity
    def test_login(self):
        # Create a test user in the database
        test_user = User(username='test_user', password='password')
        db.session.add(test_user)
        db.session.commit()

        # Test login with correct login details
        response = self.app.post('/', data={'username': 'test_user', 'password': 'password'}, follow_redirects=True)
        # Verify that the response is a successful login
        self.assertEqual(response.status_code, 200)

        # Test login with wrong username
        response = self.app.post('/', data={'username': 'wrong_username', 'password': 'password'}, follow_redirects=True)
        # Verify that the response is a failed login
        self.assertEqual(response.status_code, 200)  

        # Test login with wrong password
        response = self.app.post('/', data={'username': 'test_user', 'password': 'wrong_password'}, follow_redirects=True)
        # Verify that the response is a successful login
        self.assertEqual(response.status_code, 200)  

        # Delete the test user from the database
        db.session.delete(test_user)
        db.session.commit()

    # Test for registration
    def test_registration(self):
        # Test registration with matching passwords
        response = self.app.post('/register', data={'uName': 'test_user', 'password': 'password', 'retypePassword': 'password'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data) # Check if redirected to Login page
        self.assertIsNotNone(User.query.filter_by(username='test_user').first()) # Check if test_user is added to database

        # Test registration with non-matching passwords
        response = self.app.post('/register', data={'uName': 'test_user', 'password': 'password', 'retypePassword': 'wrong_password'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b'Passwords do not match!', response.data) 

        # Delete test_user from the database
        test_user = User.query.filter_by(username='test_user').first()
        db.session.delete(test_user)
        db.session.commit()

    # Testing access to chatroom
    def test_chatroom_redirect_if_not_logged_in(self):
        response = self.app.get('/chatroom')
        self.assertEqual(response.status_code, 302)  # Check if the page was redirected
        self.assertIn('/', response.location)   # Check if redirected to login page

    def test_chatroom_served_when_logged_in(self):
        # Create a test user
        test_user = User(username='test_user', password='password')
        db.session.add(test_user)
        db.session.commit()

        # Log in the test user
        with self.app as c:
            response = c.post('/', data={'username': 'test_user', 'password': 'password'}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)  # Check if login was successful

            # After login, make a GET request to the chatroom page
            response = c.get('/chatroom')
            self.assertEqual(response.status_code, 200)  # Check if the request was successful
            self.assertIn(b'Chatroom', response.data)  # Check if redirected to chatroom
        
        # Delete test_user
        db.session.delete(test_user)
        db.session.commit()

    # Test for logout
    def test_logout(self):
        # Log in as a user (simulating authentication)
        with self.app.session_transaction() as session:
            session['username'] = 'test_user'
        
        # Request to logout
        response = self.app.get('/logout', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200) # Check for successful request
        self.assertIn(b'Login', response.data) # Check if redirected to Login page

    # Test for creating chat with non-existing user
    def test_create_chat_with_non_existing_user(self):
        # Create test user
        test_user = User(username='test_user', password='password')
        db.session.add(test_user)
        db.session.commit()

        # Log in as the test user by sending a POST request to the login route
        login_data = {
            'username': 'test_user',
            'password': 'password'
        }
        self.app.post('/', data=login_data, follow_redirects=True)

        # Prepare data to create chat with non-existing user
        chat_data = {
            'chat_name': 'non_existing_user'
        }

        # Send a POST request to create_chat route
        response = self.app.post('/create_chat', json=chat_data)

        # Check if response say that the user does not exist
        self.assertIn(b'non_existing_user does not have an account', response.data)

        # Delete test
        db.session.delete(test_user)
        db.session.commit()
    
    # Test for successful chat creation and restrict duplicate chat creation
    def test_create_duplicate_chat(self):
        # Create a test users
        test_user = User(username='test_user', password='password')
        test_user2 = User(username='test_user2', password='password')
        db.session.add(test_user)
        db.session.add(test_user2)
        db.session.commit()

        # Log in as the test user
        self.app.post('/', data={'username': 'test_user', 'password': 'password'}, follow_redirects=True)

        # Prepare data for creating a chat
        chat_data = {'chat_name': 'test_user2'}

        # Test for successful chat creation
        response1 = self.app.post('/create_chat', json=chat_data)
        self.assertEqual(response1.status_code, 200)
        self.assertIn(b"Chat created successfully", response1.data)

        # Attempt to create a second chat with the same name
        response2 = self.app.post('/create_chat', json=chat_data)
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b"Chat with test_user2 already exists", response2.data)

    # Test for deleing chats
    def test_delete_chat(self):
        # Create test user
        test_user = User(username='test_user', password='password')
        test_user2 = User(username='test_user2', password='password')
        db.session.add(test_user)
        db.session.add(test_user2)
        db.session.commit()

        # Log in as the test user
        login_data = {
            'username': 'test_user',
            'password': 'password'
        }
        self.app.post('/', data=login_data, follow_redirects=True)

        # Create a test chat
        chat = Chats(chat_name='test_user2', receiver_chat_name='test_user', created_by=test_user.id, created_at=datetime.now())
        db.session.add(chat)
        db.session.commit()

        # Prepare data for deleting the chat
        delete_data = {
            'chat_id': chat.chat_id
        }

        # Send a DELETE request to the /chats route
        response = self.app.delete('/chats', json=delete_data)

        # Check if the chat deleted successfully
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Chat deleted successfully', response.data)

        # Clean up test data
        db.session.delete(test_user)
        db.session.delete(test_user2)
        db.session.commit()

    # Test for sending messages
    def test_send_message(self):
        # Create test users
        test_sender = User(username='test_sender', password='password')
        test_receiver = User(username='test_receiver', password='password')
        db.session.add(test_sender)
        db.session.add(test_receiver)
        db.session.commit()

        # Login as the sender
        self.app.post('/', data={'username': 'test_sender', 'password': 'password'}, follow_redirects=True)

        # Create a chat 
        chat = Chats(chat_name='test_receiver', receiver_chat_name='sender', created_by=test_sender.id, created_at=datetime.now())
        db.session.add(chat)
        db.session.commit()

        # Link the chat to in UserChat model
        sender_user_chat = UserChat(user_id=test_sender.id, chat_id=chat.chat_id)
        receiver_user_chat = UserChat(user_id=test_receiver.id, chat_id=chat.chat_id)
        db.session.add(sender_user_chat)
        db.session.add(receiver_user_chat)
        db.session.commit()

        # Prepare data for sending a message
        message_data = {
            'message': 'Test message',
            'chat_name': 'test_receiver'
        }

        # Send a POST request to send_message route
        response = self.app.post('/send_message', json=message_data)

        # Check if the message was sent successfully
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Message sent successfully", response.data)

        # Check that the message was added to the database
        sent_message = Message.query.filter_by(sender_id=test_sender.id, chat_id=chat.chat_id, msg_text='Test message').first()
        self.assertIsNotNone(sent_message)

        # Delete added data
        # Delete messages first - avoids foreign key issues
        messages = Message.query.filter_by(chat_id=chat.chat_id).all()
        for message in messages:
            db.session.delete(message)
        db.session.commit()

        db.session.delete(sender_user_chat)
        db.session.delete(receiver_user_chat)
        db.session.delete(test_sender)
        db.session.delete(test_receiver)
        db.session.delete(chat)
        db.session.commit()

    # Test for uploading files
    def test_upload_file(self):
        # Create test users
        test_sender = User(username='test_sender', password='password')
        test_receiver = User(username='test_receiver', password='password')
        db.session.add(test_sender)
        db.session.add(test_receiver)
        db.session.commit()

        # Login as the sender
        self.app.post('/', data={'username': 'test_sender', 'password': 'password'}, follow_redirects=True)

        # Create a chat
        chat = Chats(chat_name='test_receiver', receiver_chat_name='test_sender', created_by=test_sender.id, created_at=datetime.now())
        db.session.add(chat)
        db.session.commit()

        # Link the chat to UserChat model
        sender_user_chat = UserChat(user_id=test_sender.id, chat_id=chat.chat_id)
        receiver_user_chat = UserChat(user_id=test_receiver.id, chat_id=chat.chat_id)
        db.session.add(sender_user_chat)
        db.session.add(receiver_user_chat)
        db.session.commit()

        # Prepare data for file upload
        data = {
            'chat_name': 'test_receiver'
        }
        file_data = {
            'file': (BytesIO(b'this is a test file'), 'test_file.txt')
        }

        # Send a POST request to upload_file route
        response = self.app.post('/upload', data={**data, **file_data}, content_type='multipart/form-data')

        # Check if the file was uploaded successfully
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"File uploaded successfully", response.data)

        # Verify the file exists in the upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test_file.txt')
        self.assertTrue(os.path.exists(file_path))

        # Verify the message was added to the database
        sent_message = Message.query.filter_by(sender_id=test_sender.id, chat_id=chat.chat_id, file_name='test_file.txt').first()
        self.assertIsNotNone(sent_message)

        # Delete added data
        # Delete messages first - avoids foreign key issues
        messages = Message.query.filter_by(chat_id=chat.chat_id).all()
        for message in messages:
            db.session.delete(message)
        db.session.commit()

        db.session.delete(sender_user_chat)
        db.session.delete(receiver_user_chat)
        db.session.delete(chat)
        db.session.delete(test_sender)
        db.session.delete(test_receiver)
        db.session.commit()

        # Remove uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    unittest.main()
