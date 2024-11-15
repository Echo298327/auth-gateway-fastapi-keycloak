from mongoengine import Document, StringField, EmailField, ValidationError


class User(Document):
    user_name = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    role_id = StringField(required=True)
    email = EmailField(required=True)
    keycloak_uid = StringField(required=False)
    creation_date = StringField(required=True)

    def clean(self):
        if not self.keycloak_uid:
            raise ValidationError("keycloak_uid must be provided.")

    meta = {
        'collection': 'users'
    }









