__author__ = 'Cesar'


from flask_wtf import Form
from wtforms import SelectField, StringField
from wtforms.validators import Regexp, DataRequired

class ReadingForm(Form):

    outcomes = [('train', 'Training'),
                ('pic', 'Bad picture'),
                ('crop', 'Bad Cropping')]

    options_size = len(outcomes)

    reading = StringField(label='Type Reading Here!',
                          validators=[Regexp('^\d{5}$', message='Enter a valid 5 digit number'),
                                      DataRequired(message='Please enter a 5 digit number')])
    outcome = SelectField(label='What should we do!??',
                          choices=outcomes,
                          validators=[DataRequired(message='What should we do!! .. Panic!!')])
