from sqlalchemy.orm import Session

from app.models.models import Organization


class OrganizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_slug(self, slug: str) -> Organization | None:
        return self.db.query(Organization).filter(Organization.slug == slug).first()

    def add(self, organization: Organization) -> Organization:
        self.db.add(organization)
        return organization
