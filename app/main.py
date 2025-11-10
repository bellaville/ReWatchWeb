from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_required, current_user
import time, random

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('home.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

@main.route('/patient_details')
@login_required
def patient_details():
    return render_template('patient_details.html')

@main.route('/assessments')
#@login_required
def assessments():
    return render_template('assessments.html')

##########################
# SHORT TERM MEMORY TEST #
##########################
SHAPES = ['circle', 'square', 'triangle', 'star']
NUM_ROUNDS = 5

def generate_positions(num_shapes, frame_width=400, frame_height=300, shape_size=50):
    """Generate random top/left positions for shapes inside the frames
    """
    positions = []

    attempts_limit = 100  # prevent infinite loops
    for _ in range(num_shapes):
        attempts = 0
        while attempts < attempts_limit:
            top = random.randint(0, frame_height - shape_size)
            left = random.randint(0, frame_width - shape_size)
            new_frame = (top, left, top + shape_size, left + shape_size)

            # check overlap with existing shapes
            overlap = False
            for pos in positions:
                existing_frame = (pos['top'], pos['left'], pos['top'] + shape_size, pos['left'] + shape_size)
                # check if shape frame overlaps
                if not (new_frame[2] <= existing_frame[0] or  # new bottom <= existing top
                        new_frame[0] >= existing_frame[2] or  # new top >= existing bottom
                        new_frame[3] <= existing_frame[1] or  # new right <= existing left
                        new_frame[1] >= existing_frame[3]):   # new left >= existing right
                    overlap = True
                    break

            if not overlap:
                positions.append({'top': top, 'left': left})
                break
            attempts += 1

        # if we can't find a non-overlapping spot after many attempts, just place it anyway
        if attempts == attempts_limit:
            positions.append({'top': top, 'left': left})
    return positions

@main.route('/assessments/memory_test/start')
#@login_required
def start_memory_test():
    """ Initializes a short term memory test session for the current user.

    Establishes a Flask session to store temporary test metrics for a user,
    allowing the memory test to track progress and user responses
    throughout multiple rounds.
    """
    # initialize session variables
    session['round'] = 0
    session['score'] = 0
    session['reaction_times'] = []
    session['show_test'] = False # don't show the test frame yet

    # flash instructions
    flash(
        "You will see a set of shapes to memorize for 5 seconds. "
        "After that, a new set will appear. Decide if the shapes are the same or different. "
        "Your reaction time will be recorded. Are you ready to start?",
        "memory_test"
    )

    return render_template('memory_test.html', show_test=False)

@main.route('/assessments/memory_test/memorize')
def memory_memorize():
    """ Memorization phase
        - 10 second pause to memorize set of shapes
    """
    if 'round' not in session or session['round'] >= NUM_ROUNDS:
        return redirect(url_for('main.memory_result'))
    
    # pick a random set of shapes for the user to memorize
    current_set = random.sample(SHAPES, 3)
    session['previous_set'] = current_set
    session['current_set'] = current_set

    # generate random positions for the shapes in the test frame
    shape_positions = generate_positions(len(current_set))

    return render_template('memory_memorize.html', shapes=current_set, round_num=session['round']+1, shape_positions=shape_positions)


@main.route('/assessments/memory_test', methods=['GET', 'POST'])
#@login_required
def memory_test():
    """ Comparison phase where user responds
    """
    # if session doesn't have a round counter or all rounds are complete,
    # redirect user to the results page
    if 'round' not in session or session['round'] >= NUM_ROUNDS:
        return redirect(url_for('main.memory_result'))
    
    if request.method == 'POST':
        # handle user's answer
        choice = request.form.get('choice')
        reaction_time = time.time() - session['start_time']
        session['reaction_times'].append(reaction_time)

        # retrieve previous and current shape sets from the session,
        # check if current matches previous set to evaluate if user
        # is correct with their choice of "Same" or "Different"
        prev_set = session['previous_set']
        current_set = session['current_set']
        correct = (prev_set == current_set)
        if (choice == 'Same' and correct) or (choice == 'Different' and not correct):
            session['score'] += 1

        session['round'] += 1
        return redirect(url_for('main.memory_memorize')) # start next round with memorization
    
    # display comparison set
    prev_set = session['previous_set']
    # make it a 50% chance to show the same or a new set:
    if random.random() < 0.5:
        current_set = prev_set.copy()

    else:
        current_set = random.sample(SHAPES, 3)

    session['current_set'] = current_set
    session['start_time'] = time.time() # start timing reaction
    buttons_enabled = True

    # Generate random positions
    shape_positions = generate_positions(len(current_set))

    return render_template('memory_test.html', shapes=current_set, round_num=session['round']+1, buttons_enabled=buttons_enabled, show_test=True, shape_positions=shape_positions)

@main.route('/assessments/memory_test/result')
#@login_required
def memory_result():
    avg_reaction = sum(session.get('reaction_times', [])) / max(len(session.get('reaction_times', [])), 1)
    score = session.get('score', 0)
    return render_template('memory_result.html', score=score, avg_reaction=avg_reaction)

