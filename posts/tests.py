from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from posts.models import Post, Comment
from notifications.models import Notification

class PostsViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        # Create a post
        self.post = Post.objects.create(author=self.user1, content='Hello World')

    def test_home_feed_unauthenticated(self):
        """Test that unauthenticated users can access the home page."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/welcome.html')
        self.assertNotIn('posts', response.context)

    def test_home_feed_authenticated(self):
        """Test that authenticated users see posts in home feed."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/home.html')
        self.assertIn('posts', response.context)
        self.assertEqual(response.context['posts'].count(), 1)

    def test_post_create(self):
        """Test creating a post via POST request."""
        self.client.login(username='user1', password='password123')
        data = {'content': 'My second post'}
        response = self.client.post(reverse('post_create'), data=data)
        self.assertEqual(response.status_code, 302) # Redirect to home
        self.assertEqual(Post.objects.count(), 2)
        self.assertTrue(Post.objects.filter(content='My second post').exists())

    def test_post_detail(self):
        """Test viewing post details and comments."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('post_detail', kwargs={'pk': self.post.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'posts/post_detail.html')
        self.assertEqual(response.context['post'], self.post)

    def test_post_delete(self):
        """Test that author can delete their post, but others cannot."""
        # Try as user2 first (should not delete)
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(Post.objects.count(), 1)
        
        # Try as user1 (author, should delete)
        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('post_delete', kwargs={'pk': self.post.pk}))
        self.assertEqual(Post.objects.count(), 0)

    def test_post_like_toggle(self):
        """Test reacting/un-reacting on a post, and that notification is sent to author."""
        self.client.login(username='user2', password='password123')
        # React to the post
        response = self.client.post(reverse('post_react', kwargs={'pk': self.post.pk}), data={'reaction_type': 'like'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['reacted'], True)
        self.assertEqual(response.json()['reaction_type'], 'like')
        self.assertEqual(self.post.reaction_count(), 1)
        # Check notification was created
        self.assertTrue(Notification.objects.filter(
            recipient=self.user1,
            sender=self.user2,
            notification_type='like',
            post=self.post
        ).exists())

        # Un-react the post
        response = self.client.post(reverse('post_react', kwargs={'pk': self.post.pk}), data={'reaction_type': 'like'})
        self.assertEqual(response.json()['reacted'], False)
        self.assertEqual(self.post.reaction_count(), 0)

    def test_add_comment(self):
        """Test adding a comment and notification to post author."""
        self.client.login(username='user2', password='password123')
        data = {'content': 'Cool post!'}
        response = self.client.post(reverse('add_comment', kwargs={'pk': self.post.pk}), data=data)
        self.assertEqual(response.status_code, 302) # Redirect to detail view
        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(Comment.objects.filter(content='Cool post!').exists())
        # Check notification
        self.assertTrue(Notification.objects.filter(
            recipient=self.user1,
            sender=self.user2,
            notification_type='comment',
            post=self.post
        ).exists())

    def test_mentions_create_notifications(self):
        """Test @mentions in posts and comments notify mentioned users."""
        self.client.login(username='user1', password='password123')
        response = self.client.post(
            reverse('post_create'),
            data={'content': 'Hello @user2, check this out #django'}
        )
        self.assertEqual(response.status_code, 302)
        mentioned_post = Post.objects.latest('id')
        self.assertTrue(Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            notification_type='mention',
            post=mentioned_post,
        ).exists())

        self.client.login(username='user2', password='password123')
        response = self.client.post(
            reverse('add_comment', kwargs={'pk': self.post.pk}),
            data={'content': 'Thanks @user1'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(
            recipient=self.user1,
            sender=self.user2,
            notification_type='mention',
            post=self.post,
        ).exists())

    def test_search(self):
        """Test search query searches username and post content."""
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('search') + '?q=Hello')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.post, response.context['posts_results'])
        
        response = self.client.get(reverse('search') + '?q=user2')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.user2, response.context['users_results'])

    def test_create_poll(self):
        """Test that creating a poll saves the Post, Poll, and PollOption objects."""
        self.client.login(username='user1', password='password123')
        data = {
            'content': 'Check this poll out!',
            'question': 'What is your favorite framework?',
            'options': ['Django', 'FastAPI', 'Flask']
        }
        response = self.client.post(reverse('create_poll'), data=data)
        self.assertEqual(response.status_code, 302)  # Redirects to home
        
        # Verify database objects
        from posts.poll_models import Poll
        self.assertEqual(Poll.objects.count(), 1)
        poll = Poll.objects.first()
        self.assertEqual(poll.question, 'What is your favorite framework?')
        self.assertEqual(poll.options.count(), 3)
        self.assertEqual(poll.post.content, 'Check this poll out!')

    def test_vote_poll(self):
        """Test voting in a poll increments vote count and prevents double voting."""
        from posts.poll_models import Poll, PollOption, PollVote
        poll = Poll.objects.create(post=self.post, question='Test Poll')
        opt1 = PollOption.objects.create(poll=poll, text='Yes')
        opt2 = PollOption.objects.create(poll=poll, text='No')
        
        # Vote 1: user2 votes Yes
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('vote_poll', kwargs={'pk': poll.pk}), data={'option_id': opt1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['success'], True)
        self.assertEqual(PollVote.objects.count(), 1)
        
        opt1.refresh_from_db()
        self.assertEqual(opt1.vote_count, 1)
        self.assertEqual(poll.total_votes(), 1)
        
        # Vote 2: user2 tries to vote again (should fail)
        response = self.client.post(reverse('vote_poll', kwargs={'pk': poll.pk}), data={'option_id': opt2.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['success'], False)
        self.assertEqual(PollVote.objects.count(), 1)



    def test_post_create_collaborative(self):
        """Test creating a post with a co-author and that notification is sent."""
        self.client.login(username='user1', password='password123')
        data = {
            'content': 'Collab post content',
            'co_author_id': self.user2.id
        }
        response = self.client.post(reverse('post_create'), data=data)
        self.assertEqual(response.status_code, 302) # Redirect to home
        self.assertEqual(Post.objects.count(), 2)
        
        post = Post.objects.filter(content='Collab post content').first()
        self.assertIsNotNone(post)
        self.assertIn(self.user2, post.co_authors.all())
        
        # Verify notification created
        self.assertTrue(Notification.objects.filter(
            recipient=self.user2,
            sender=self.user1,
            notification_type='collab_invite',
            post=post
        ).exists())

    def test_collab_post_shows_in_both_feeds(self):
        """Test that a co-authored post appears in the feed and profiles of both authors."""
        collab_post = Post.objects.create(author=self.user1, content='Shared collab')
        collab_post.co_authors.add(self.user2)
        
        # Check user1 profile views
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('profile', kwargs={'username': 'user1'}))
        self.assertIn(collab_post, response.context['posts'])
        
        # Check user2 profile views
        self.client.login(username='user2', password='password123')
        response = self.client.get(reverse('profile', kwargs={'username': 'user2'}))
        self.assertIn(collab_post, response.context['posts'])
        
        # Check user2 home feed (since they are co-author, it must show up)
        response = self.client.get(reverse('home'))
        self.assertIn(collab_post, response.context['posts'])

