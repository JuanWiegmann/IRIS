"""
Test Use Case Detection
========================

Tests for routing validation based on content type.
"""

import pytest
from src.validation import UseCase, detect_use_case


# ═══════════════════════════════════════════════════════════
# MESSAGING USE CASE TESTS
# ═══════════════════════════════════════════════════════════

def test_detect_messaging_email():
    """Detect simple email as messaging."""
    query = "Write an email to the team about project status"
    draft = """Hi Team,

Quick update on the project:
• Milestone 1 complete
• Working on Milestone 2
• On track for delivery

Let me know if questions!
"""

    assert detect_use_case(query, draft) == UseCase.MESSAGING


def test_detect_messaging_document():
    """Detect document as messaging."""
    query = "Write meeting notes"
    draft = """Meeting Notes - 2026-09-02

Attendees: Alice, Bob, Charlie

Discussion:
- Project timeline review
- Resource allocation
- Next steps

Action Items:
- Alice: Update documentation
- Bob: Review code changes
"""

    assert detect_use_case(query, draft) == UseCase.MESSAGING


# ═══════════════════════════════════════════════════════════
# CODING USE CASE TESTS
# ═══════════════════════════════════════════════════════════

def test_detect_coding_python():
    """Detect Python code as coding."""
    query = "Write a function to sort users by age"
    draft = """```python
def sort_users_by_age(users):
    \"\"\"Sort users by age in ascending order.\"\"\"
    return sorted(users, key=lambda u: u['age'])
```
"""

    assert detect_use_case(query, draft) == UseCase.CODING


def test_detect_coding_javascript():
    """Detect JavaScript code as coding."""
    query = "Create a React component for user list"
    draft = """```javascript
function UserList({ users }) {
  return (
    <div className="user-list">
      {users.map(user => (
        <div key={user.id}>{user.name}</div>
      ))}
    </div>
  );
}
```
"""

    assert detect_use_case(query, draft) == UseCase.CODING


def test_detect_coding_without_code_block():
    """Detect code without code block markers."""
    query = "Fix the login function"
    draft = """async function login(username, password) {
  const response = await fetch('/api/auth', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  });
  return response.json();
}
"""

    assert detect_use_case(query, draft) == UseCase.CODING


def test_detect_coding_file_extension():
    """Detect code from file extension mention."""
    query = "Update the server.py file to add logging"
    draft = """Add the following to server.py:

import logging
logging.basicConfig(level=logging.INFO)
"""

    assert detect_use_case(query, draft) == UseCase.CODING


# ═══════════════════════════════════════════════════════════
# MENDIX USE CASE TESTS
# ═══════════════════════════════════════════════════════════

def test_detect_mendix_domain_model():
    """Detect Mendix domain model XML."""
    query = "Create a User entity in Mendix"
    draft = """<entity name="User">
  <attributes>
    <attribute name="Name" type="String" />
    <attribute name="Email" type="String" />
    <attribute name="Age" type="Integer" />
  </attributes>
</entity>
"""

    assert detect_use_case(query, draft) == UseCase.MENDIX


def test_detect_mendix_microflow():
    """Detect Mendix microflow reference."""
    query = "Help me design a microflow for user creation"
    draft = """Create a microflow called ACT_User_Create:

1. Retrieve current user
2. Create new User entity
3. Set attributes from input
4. Commit User
5. Show success message
"""

    assert detect_use_case(query, draft) == UseCase.MENDIX


def test_detect_mendix_keywords():
    """Detect Mendix from keyword density."""
    query = "Explain Mendix domain model best practices"
    draft = """Best practices for Mendix domain models:

1. Entity naming: Use singular nouns (e.g., 'Customer' not 'Customers')
2. Associations: Always define both directions
3. Attributes: Use appropriate data types
4. Microflows: Keep them focused and reusable
5. Modules: Organize by business domain
"""

    assert detect_use_case(query, draft) == UseCase.MENDIX


def test_detect_mendix_widget():
    """Detect Mendix widget development."""
    query = "Create a custom Mendix widget"
    draft = """To create a custom Mendix widget:

1. Use the Mendix Widget Generator
2. Define widget.xml configuration
3. Implement component logic
4. Package as .mpk file
5. Import into your Mendix app
"""

    assert detect_use_case(query, draft) == UseCase.MENDIX


# ═══════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════

def test_detect_code_in_email():
    """Code snippet in email should be detected as coding."""
    query = "Email Bob about the bug fix"
    draft = """Hi Bob,

I fixed the login bug. Here's the change:

```python
def login(username, password):
    if not username or not password:
        raise ValueError("Missing credentials")
    return authenticate(username, password)
```

Let me know if this works!
"""

    # Code block should dominate
    assert detect_use_case(query, draft) == UseCase.CODING


def test_detect_mendix_with_code():
    """Mendix content with code should be detected as Mendix."""
    query = "Show me how to use JavaScript in Mendix"
    draft = """In Mendix, you can use JavaScript actions:

<microflow name="ProcessData">
  <activities>
    <javascriptAction>
      function processData(data) {
        return data.map(item => item.value * 2);
      }
    </javascriptAction>
  </activities>
</microflow>
"""

    # Mendix should dominate (more specific)
    assert detect_use_case(query, draft) == UseCase.MENDIX


def test_detect_ambiguous_defaults_to_messaging():
    """Ambiguous content defaults to messaging."""
    query = "Help me understand this"
    draft = """This is a general explanation about something
without clear indicators of code or Mendix.
"""

    assert detect_use_case(query, draft) == UseCase.MESSAGING
