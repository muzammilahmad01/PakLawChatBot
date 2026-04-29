import pytest
import sys
import os

# Add ChatBot directory to sys.path so we can import backend logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../ChatBot')))

from chatbotlogic import is_off_topic

def test_is_off_topic_greetings():
    # Greetings should be flagged as off-topic to skip RAG
    assert is_off_topic("hello") == True
    assert is_off_topic("good morning bot") == True
    assert is_off_topic("assalam o alaikum") == True

def test_is_off_topic_math():
    # Math questions should be flagged as off-topic
    assert is_off_topic("what is 5+7") == True
    assert is_off_topic("calculate 20 * 4") == True
    assert is_off_topic("100 / 2") == True

def test_is_not_off_topic_legal_queries():
    # Actual legal questions should NOT be flagged as off-topic
    assert is_off_topic("What is Section 302 of PPC?") == False
    assert is_off_topic("Tell me about fundamental rights in the constitution.") == False
    assert is_off_topic("How to get bail in Pakistan?") == False
    assert is_off_topic("what is cyber crime") == False

def test_is_off_topic_edge_cases():
    # Edge cases
    assert is_off_topic("   HELLO   ") == True
    assert is_off_topic("WHAT IS 10-5") == True
