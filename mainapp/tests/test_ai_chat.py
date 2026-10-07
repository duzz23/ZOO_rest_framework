"""Tests for AI chat view."""
from django.test import TestCase, Client
from unittest.mock import patch
import json


class TestAIChatView(TestCase):

    def setUp(self):
        self.client = Client()

    @patch('mainapp.views.ask_ai')
    def test_ai_chat_success(self, mock_ask_ai):
        """Test successful AI response."""
        mock_ask_ai.return_value = "This is an answer from the AI."
        response = self.client.post(
            '/ai-chat/',
            data=json.dumps({"question": "What is Antarctic Wallet?"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("answer", data)
        self.assertEqual(data["answer"], "This is an answer from the AI.")

    @patch('mainapp.views.ask_ai')
    def test_ai_chat_empty_question(self, mock_ask_ai):
        """Test that empty question returns 400."""
        response = self.client.post(
            '/ai-chat/',
            data=json.dumps({"question": ""}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)

    @patch('mainapp.views.ask_ai')
    def test_ai_chat_missing_question(self, mock_ask_ai):
        """Test that missing question key returns 400."""
        response = self.client.post(
            '/ai-chat/',
            data=json.dumps({}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    @patch('mainapp.views.ask_ai')
    def test_ai_chat_get_not_allowed(self, mock_ask_ai):
        """Test that GET request returns 405 Method Not Allowed."""
        response = self.client.get('/ai-chat/')
        self.assertEqual(response.status_code, 405)
