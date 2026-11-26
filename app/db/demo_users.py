"""The demo workspace's users (build brief, section 15). Demo data only: not real people."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoUser:
    email: str
    display_name: str
    role: str
    groups: tuple[str, ...]
    is_active: bool = True


DEMO_USERS = (
    DemoUser("alice@demo.local", "Alice", "employee", ("everyone",)),
    DemoUser("bob@demo.local", "Bob", "helpdesk", ("everyone", "helpdesk")),
    DemoUser("carol@demo.local", "Carol", "security_admin", ("everyone", "security")),
    DemoUser("dave@demo.local", "Dave", "hr", ("everyone", "hr")),
    DemoUser("erin@demo.local", "Erin", "employee", ("everyone",), is_active=False),
)