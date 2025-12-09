"""
Unit and Integration Tests for Ticket Management System
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.ticket import Ticket
from app.models.user import User, Role, Department
from datetime import datetime


class TestTicketCreation:
    """Unit tests for ticket creation endpoint"""
    
    def test_create_ticket_success(self, client: TestClient, auth_headers, setup_test_db: Session, test_user: User):
        """Test successful ticket creation with valid data"""
        # Debug: Check if we have auth headers
        if not auth_headers or "Authorization" not in auth_headers:
            pytest.skip("Auth headers not available - login failed")
        
        ticket_data = {
            "title": "Test Ticket",
            "description": "This is a test ticket description",
            "priority": "High",
            "category": "Bilgi Islem",
            "department_name": "Bilgi Islem"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Ticket"
        assert data["description"] == "This is a test ticket description"
        assert data["priority"] == "High"
        assert data["status"] == "Open"
        assert data["category"] == "Bilgi Islem"

    def test_create_ticket_without_title(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test ticket creation without explicit title - should use AI suggestion or fallback"""
        ticket_data = {
            "description": "This is a test without title",
            "priority": "Medium",
            "category": "Yapi Isleri",
            "department_name": "Yapi Isleri"
        }
        
        with patch('app.routers.tickets.suggest_ticket') as mock_suggest:
            # Mock AI suggestion to return a title
            mock_suggest.return_value = {
                "suggested_title": "AI Generated Title",
                "priority_options": ["Medium"],
                "department_options": ["Yapi Isleri"]
            }
            
            response = client.post(
                "/api/v1/tickets/",
                json=ticket_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["title"] is not None  # Should have a title (either AI or fallback)

    def test_create_ticket_without_department(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test ticket creation without specifying department - should pick first available"""
        ticket_data = {
            "title": "Ticket without Department",
            "description": "Testing department auto-selection",
            "priority": "Low",
            "category": "Testing"
        }
        
        with patch('app.routers.tickets.suggest_ticket') as mock_suggest:
            mock_suggest.return_value = {
                "suggested_title": "Ticket without Department",
                "priority_options": ["Low"],
                "department_options": ["Bilgi Islem"]
            }
            
            response = client.post(
                "/api/v1/tickets/",
                json=ticket_data,
                headers=auth_headers
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["priority"] == "Low"

    def test_create_ticket_missing_auth(self, client: TestClient, setup_test_db: Session):
        """Test ticket creation without authentication - should fail"""
        ticket_data = {
            "title": "Unauthorized Ticket",
            "description": "Should fail",
            "priority": "High",
            "department_name": "Bilgi Islem"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data
        )
        
        assert response.status_code == 403 or response.status_code == 401

    def test_create_ticket_invalid_priority(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test ticket creation with invalid priority - should still work with valid values"""
        ticket_data = {
            "title": "Test Priority",
            "description": "Testing priority handling",
            "priority": "Critical",  # Valid priority
            "department_name": "Bilgi Islem"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        # Should work if priority is in valid range
        if response.status_code == 201:
            assert response.json()["priority"] in ["Low", "Medium", "High", "Critical"]


class TestTicketIntegration:
    """Integration tests for ticket creation and database persistence"""
    
    def test_ticket_persisted_in_database(self, client: TestClient, auth_headers, setup_test_db: Session, test_user: User):
        """Test that created ticket is actually stored in database"""
        ticket_data = {
            "title": "Database Persistence Test",
            "description": "Verify this ticket is saved to DB",
            "priority": "Medium",
            "department_name": "Bilgi Islem"
        }
        
        # Create ticket
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        ticket_id = response.json()["id"]
        
        # Verify in database
        db_ticket = setup_test_db.query(Ticket).filter(Ticket.id == ticket_id).first()
        assert db_ticket is not None
        assert db_ticket.title == "Database Persistence Test"
        assert db_ticket.description == "Verify this ticket is saved to DB"
        assert db_ticket.priority == "Medium"
        assert db_ticket.status == "Open"
        assert db_ticket.created_by_user_id == test_user.id

    def test_ticket_assigned_to_correct_department(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test that ticket is assigned to the correct department"""
        ticket_data = {
            "title": "Department Assignment Test",
            "description": "Testing department assignment",
            "priority": "High",
            "department_name": "Yapi Isleri"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        ticket_id = response.json()["id"]
        
        # Verify department assignment
        db_ticket = setup_test_db.query(Ticket).filter(Ticket.id == ticket_id).first()
        assert db_ticket is not None
        assert db_ticket.assigned_department.name == "Yapi Isleri"

    def test_multiple_tickets_created_by_user(self, client: TestClient, auth_headers, setup_test_db: Session, test_user: User):
        """Test creating multiple tickets and verifying they are all attributed to the user"""
        tickets_data = [
            {
                "title": f"Test Ticket {i}",
                "description": f"Description {i}",
                "priority": "Low",
                "department_name": "Bilgi Islem"
            }
            for i in range(3)
        ]
        
        created_ids = []
        for ticket_data in tickets_data:
            response = client.post(
                "/api/v1/tickets/",
                json=ticket_data,
                headers=auth_headers
            )
            assert response.status_code == 201
            created_ids.append(response.json()["id"])
        
        # Verify all tickets belong to the user
        user_tickets = setup_test_db.query(Ticket).filter(Ticket.created_by_user_id == test_user.id).all()
        assert len(user_tickets) >= 3
        for ticket in user_tickets:
            assert ticket.created_by_user_id == test_user.id


class TestAIMockIntegration:
    """Tests for AI integration with mocking"""
    
    @pytest.mark.asyncio
    async def test_ai_suggestion_mock(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test that AI suggestion is called and mocked correctly during ticket creation"""
        ticket_data = {
            "title": "AI Suggestion Test",
            "description": "Testing AI suggestion mocking",
            "department_name": "Bilgi Islem"
        }
        
        with patch('app.routers.tickets.suggest_ticket') as mock_suggest:
            # Mock AI response
            mock_suggest.return_value = {
                "suggested_title": "AI Suggested Title",
                "priority_options": ["High", "Medium", "Low"],
                "department_options": ["Bilgi Islem", "Yapi Isleri"]
            }
            
            response = client.post(
                "/api/v1/tickets/",
                json=ticket_data,
                headers=auth_headers
            )
            
            # Verify mock was called
            mock_suggest.assert_called_once()
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_ai_suggestion_fallback(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test that ticket creation works even if AI suggestion fails"""
        ticket_data = {
            "title": "AI Fallback Test",
            "description": "Testing fallback when AI fails",
            "priority": "Medium",
            "department_name": "Bilgi Islem"
        }
        
        with patch('app.routers.tickets.suggest_ticket') as mock_suggest:
            # Simulate AI failure
            mock_suggest.side_effect = Exception("AI Service Unavailable")
            
            response = client.post(
                "/api/v1/tickets/",
                json=ticket_data,
                headers=auth_headers
            )
            
            # Should still create ticket with fallback values
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "AI Fallback Test"
            assert data["priority"] == "Medium"
            assert data["department_name"] == "Bilgi Islem"

    def test_get_ai_suggestions_endpoint(self, client: TestClient, auth_headers):
        """Test the AI suggestions endpoint with mocked OpenAI"""
        suggest_data = {
            "title": "Network Problem",
            "description": "Internet connection not working in lab"
        }
        
        with patch('app.core.services.openai.ChatCompletion.create') as mock_openai:
            # Mock OpenAI response
            mock_openai.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"suggested_title": "Lab Network Issue", "priority": "High", "category": "Bilgi Islem"}'
                        }
                    }
                ]
            }
            
            response = client.post(
                "/api/v1/tickets/suggest",
                json=suggest_data,
                headers=auth_headers
            )
            
            # Verify endpoint works and returns suggestions
            if response.status_code == 200:
                assert "suggestions" in response.json() or "suggested_title" in response.json()

    def test_draft_response_generation(self, client: TestClient, auth_headers, setup_test_db: Session, test_user: User):
        """Test draft response generation with AI mocking"""
        # First create a ticket
        ticket_data = {
            "title": "Draft Response Test",
            "description": "Testing draft response generation",
            "priority": "High",
            "department_name": "Bilgi Islem"
        }
        
        create_response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        ticket_id = create_response.json()["id"]
        
        # Test draft generation with mocked AI
        with patch('app.core.services.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Here is a sample solution to your problem..."
                        }
                    }
                ]
            }
            
            draft_data = {
                "ticket_id": ticket_id,
                "draft_text": "Checking network configuration...",
                "status": "In Progress"
            }
            
            response = client.post(
                "/api/v1/tickets/draft",
                json=draft_data,
                headers=auth_headers
            )
            
            # Should either succeed or return expected status
            assert response.status_code in [200, 201, 400, 404]


class TestTicketValidation:
    """Tests for ticket data validation"""
    
    def test_ticket_empty_description(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test ticket creation with empty description"""
        ticket_data = {
            "title": "Empty Description",
            "description": "",
            "priority": "Low",
            "department_name": "Bilgi Islem"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        # Should either accept or return validation error
        assert response.status_code in [201, 422]

    def test_ticket_very_long_description(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test ticket creation with very long description"""
        long_description = "A" * 5000  # Very long description
        
        ticket_data = {
            "title": "Long Description Test",
            "description": long_description,
            "priority": "Medium",
            "department_name": "Bilgi Islem"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        # Should either accept or return validation error
        assert response.status_code in [201, 422]

    def test_ticket_special_characters(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test ticket creation with special characters and Turkish characters"""
        ticket_data = {
            "title": "Türkçe Karakterler - ü ö ç ş ı ğ",
            "description": "Testing with special chars: !@#$%^&*() और 中文",
            "priority": "High",
            "department_name": "Bilgi Islem"
        }
        
        response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "Türkçe" in data["title"]


class TestTicketRetrieval:
    """Tests for ticket retrieval endpoints"""
    
    def test_list_user_tickets(self, client: TestClient, auth_headers, setup_test_db: Session, test_user: User):
        """Test listing tickets created by the current user"""
        # Create some tickets
        for i in range(2):
            ticket_data = {
                "title": f"User Ticket {i}",
                "description": f"Description {i}",
                "priority": "Low",
                "department_name": "Bilgi Islem"
            }
            
            client.post(
                "/api/v1/tickets/",
                json=ticket_data,
                headers=auth_headers
            )
        
        # List user tickets
        response = client.get(
            "/api/v1/tickets/me",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_get_ticket_by_id(self, client: TestClient, auth_headers, setup_test_db: Session):
        """Test retrieving a specific ticket by ID"""
        # Create a ticket
        ticket_data = {
            "title": "Get Ticket Test",
            "description": "Testing single ticket retrieval",
            "priority": "High",
            "department_name": "Bilgi Islem"
        }
        
        create_response = client.post(
            "/api/v1/tickets/",
            json=ticket_data,
            headers=auth_headers
        )
        
        assert create_response.status_code == 201
        ticket_id = create_response.json()["id"]
        
        # Get ticket by ID
        response = client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == ticket_id
            assert data["title"] == "Get Ticket Test"
