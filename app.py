from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/patient_details')
def patient_details():
    return render_template('patient_details.html')

@app.route('/Assesments')
def assessments():
    return render_template('assessments.html')

if __name__ == "__main__":
    app.run(debug=True)
