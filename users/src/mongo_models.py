from mongoengine import Document, StringField, ListField, EmailField


class User(Document):
    user_name = StringField(required=True, unique=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    roles = ListField(StringField(choices=["admin", "user", "systemAdmin"]), required=True)
    email = EmailField(required=True, unique=True)
    keycloak_uid = StringField(required=False, unique=True)
    creation_date = StringField(required=True)

    def clean(self):
        # Always save user_name in lowercase
        if self.user_name:
            self.user_name = self.user_name.lower()

    meta = {
        'collection': 'users',
        "indexes": [
            {"fields": ["user_name"], "unique": True},  # Case-sensitive unique index
            {"fields": ["email"], "unique": True},
            {"fields": ["keycloak_uid"], "unique": True, "sparse": True},
        ],
    }
