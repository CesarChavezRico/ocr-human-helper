import config
from flask import Flask, render_template, request, redirect, url_for, session
from task import Task
from reading_form import ReadingForm
from flask_oauth import OAuth
import requests
import app_engine as backend

GOOGLE_CLIENT_ID = '382197999605-kh8uo8cup46ohrnh2hdrtakcm6f36ore.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = 'T7wNDAkD0Oi25YXmsYxYXnSu'
REDIRECT_URI = '/authorized'  # one of the Redirect URIs from Google APIs console

# setup flask
app = Flask(__name__)
app.config.update(
    SECRET_KEY='development key',
    DEBUG=True
)

oauth = OAuth()

google = oauth.remote_app('google',
                          base_url='https://www.google.com/accounts/',
                          authorize_url='https://accounts.google.com/o/oauth2/auth',
                          request_token_url=None,
                          request_token_params={'scope': 'https://www.googleapis.com/auth/userinfo.email',
                                                'response_type': 'code'},
                          access_token_url='https://accounts.google.com/o/oauth2/token',
                          access_token_method='POST',
                          access_token_params={'grant_type': 'authorization_code'},
                          consumer_key=GOOGLE_CLIENT_ID,
                          consumer_secret=GOOGLE_CLIENT_SECRET)

@app.before_request
def check_credentials():
    """

    :return:
    """
    config.logging.debug('app: check_credentials - request.endpoint: {0}'.format(request.endpoint))
    if request.endpoint == 'login' or request.endpoint == 'authorized':
        config.logging.debug('app: check_credentials - login or authorized')
    else:
        access_token = session.get('access_token')
        if access_token is None:
            return redirect(url_for('login'))
        else:
            config.logging.debug('app: check_credentials - got token!: {0}'.format(access_token))


@app.route('/')
def index():
    """

    :return:
    """
    access_token = session.get('access_token')
    access_token = access_token[0]

    headers = {'Authorization': 'OAuth '+access_token}
    r = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', headers=headers)
    config.logging.debug('app: Response from OAuth: {0}'.format(r.json()))

    if r.status_code == 401:
        # Unauthorized - bad token
        session.pop('access_token', None)
        return redirect(url_for('login'))
    else:
        if r.json()['email'] == 'cesar@golocky.com' or \
           r.json()['email'] == 'carlos@golocky.com':
            return redirect(url_for('get_next_task'))
        else:
            s = u'=(  Sorry {0} you are not allowed to help.'.format(r.json()['given_name'])
            return s


@app.route('/login')
def login():
    """

    :return:
    """
    callback = url_for('authorized', _external=True)
    return google.authorize(callback=callback)


@app.route(REDIRECT_URI)
@google.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token, ''
    return redirect(url_for('index'))


@google.tokengetter
def get_access_token():
    return session.get('access_token')


@app.route('/next_task', methods=['GET'])
def get_next_task():
    """

    :return:
    """
    try:
        next_task = Task(queue=config.QUEUE)
        if next_task is not None:
            session['task_id'] = next_task.id
            session['task_payload'] = next_task.payload
            r = ReadingForm()
            return render_template('images.html',
                                   form=r,
                                   original_image_url=next_task.image.get_public_url_original(),
                                   cropped_image_url=next_task.image.get_public_url_cropped(),
                                   height=next_task.image.pic.size[1]/4,
                                   width=next_task.image.pic.size[0]/4,
                                   task_id=next_task.id)
        else:
            return 'No tasks available'
    except TypeError:
        return 'No tasks available'


@app.route('/validate', methods=['POST'])
def validate():
    """

    :return:
    """
    r = ReadingForm()
    if r.validate_on_submit():
        config.logging.debug('app: Got in form: [{0}]'.format(r.data))
        return redirect(url_for('success', result=r.data['reading'], outcome=r.data['outcome']))
    else:
        config.logging.debug('app: Error validating form')
        task_id = request.args['task_id']
        return redirect(url_for('retry', task_id=task_id))


@app.route('/retry', methods=['GET'])
def retry():
    """

    :return:
    """
    errors = ['Something is wrong! Please try again .. ']
    task_id = request.args['task_id']
    try:
        retry_task = Task(task_id=task_id)
        if retry_task is not None:
            r = ReadingForm()
            return render_template('images.html',
                                   errors=errors,
                                   form=r,
                                   original_image_url=retry_task.image.get_public_url_original(),
                                   cropped_image_url=retry_task.image.get_public_url_cropped(),
                                   height=retry_task.image.pic.size[1]/4,
                                   width=retry_task.image.pic.size[0]/4,
                                   task_id=retry_task.id)
        else:
            return 'Task not longer available'
    except TypeError:
        return 'No tasks available'


@app.route('/success')
def success():
    """

    :return:
    """
    reading = request.args['result']
    outcome = request.args['outcome']
    config.logging.debug('app: success - Params: Reading = [{0}], Outcome = [{1}]'.format(reading, outcome))
    t = Task(task_id=session.get('task_id'))
    if outcome == 'pic':
        # Bad picture, notify error to backend
        if backend.notify_error_to_app_engine(error='No podemos identificar digitos en la fotografia',
                                              task_name=t.id,
                                              task_payload=t.payload):
            config.logging.debug('app: success - Error sent to app_engine Backend')
            config.logging.debug('app: success - Deleting task {0} from queue'.format(t.id))
            t.delete_task_from_queue()

    elif outcome == 'train':
        # Engine needs training, send read digits to customer
        if backend.post_result_to_app_engine(result=reading,
                                             task_name=t.id,
                                             task_payload=t.payload):
            config.logging.debug('app: success - Training needed - Result sent to app_engine Backend')
            config.logging.debug('app: success - Moving task {0} to training queue'.format(t.id))
            # TODO: What data do we need for the automated training??
            payload = {"result": reading}
            t.move_to_queue('training', payload, config.TRAINING_LEASE_TIME)

    elif outcome == 'crop':
        # Engine needs better cropping, send read digits to customer
        if backend.post_result_to_app_engine(result=reading,
                                             task_name=t.id,
                                             task_payload=t.payload):
            config.logging.debug('app: success - Better Cropping needed - Result sent to app_engine Backend')
            config.logging.debug('app: success - Moving task {0} to improve_cropping queue'.format(t.id))
            # TODO: What data do we need????
            payload = ''' {
                           result = {0}
                           }'''.format(reading)
            t.move_to_queue('improve_cropping', payload, config.CROPPING_LEASE_TIME)

    session['task_id'] = None
    session['task_payload'] = None
    return render_template('success.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
