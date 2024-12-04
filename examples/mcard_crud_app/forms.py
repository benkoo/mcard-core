"""Forms for the MCard CRUD application."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

class TextCardForm(FlaskForm):
    """Form for creating a text card."""
    content = TextAreaField('Text Content', 
                             validators=[DataRequired(message="Content cannot be empty"), 
                                         Length(min=1, max=10000, 
                                                message="Content must be between 1 and 10000 characters")])

class FileCardForm(FlaskForm):
    """Form for uploading a file card."""
    file = FileField('Upload File', 
                     validators=[DataRequired(message="Please select a file to upload")])

    def validate_file(self, field):
        """Custom validation to ensure file is not empty."""
        if not field.data:
            raise ValidationError("Please select a file to upload")
        
        # Optional: Add file size limit
        if hasattr(field.data, 'content_length'):
            if field.data.content_length > 10 * 1024 * 1024:  # 10 MB limit
                raise ValidationError("File size must be less than 10 MB")

class DeleteCardForm(FlaskForm):
    """Form for deleting a card."""
    hash = HiddenField('Card Hash', validators=[DataRequired(message="Card hash is required")])

class NewCardForm(FlaskForm):
    """Unified form for creating a new card."""
    content = TextAreaField('Content', 
                             validators=[Optional(), 
                                         Length(max=10000, 
                                                message="Content must be less than 10000 characters")])
    file = FileField('Upload File', 
                     validators=[Optional()])
    type = StringField('Card Type', 
                       validators=[Optional(), 
                                   Length(max=50, 
                                          message="Card type must be less than 50 characters")])

    def validate(self, extra_validators=None):
        """Custom validation to ensure either content or file is provided."""
        if not super().validate(extra_validators):
            return False
        
        # Check if either content or file is provided
        if not self.content.data and not self.file.data:
            self.content.errors.append('Either text content or file must be provided')
            return False
        
        return True
