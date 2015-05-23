import config
from flask import Flask, render_template, request, redirect, url_for
from task import Task
from reading_form import ReadingForm


app = Flask(__name__)
app.secret_key = 'ccr'

@app.route('/', methods=['GET'])
def get_next_task():
    """

    :return:
    """
    next_task = Task(queue=config.QUEUE)
    if next_task is not None:
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


@app.route('/validate', methods=['POST'])
def validate():
    """

    :return:
    """
    r = ReadingForm()
    if r.validate_on_submit():
        config.logging.debug('app: Got in form: [{0}]'.format(r.data))
        return redirect(url_for('success'))
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


@app.route('/success')
def success():
    """

    :return:
    """
    return render_template('success.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
